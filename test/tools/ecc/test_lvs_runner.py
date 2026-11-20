import json
from pathlib import Path
from typing import Any

import pytest

from chipcompiler.data import (
    EccData,
    EccFeature,
    EccReport,
    EccStep,
    OriginDesign,
    StepEnum,
    StepInput,
    Workspace,
)
from chipcompiler.tools.ecc import runner as ecc_runner
from chipcompiler.tools.ecc.builder import build_step, build_step_space
from chipcompiler.tools.ecc.metrics import build_metrics_lvs


class FakeLvsModule:
    def __init__(self, *, netlist_loaded=True):
        self.netlist_loaded = netlist_loaded
        self.calls = []

    def read_lvs_verilog(self, path, top_module):
        self.calls.append(("read_lvs_verilog", path, top_module))
        return self.netlist_loaded

    def update_step_paths(self, **kwargs):
        self.calls.append(("update_step_paths", kwargs))

    def init_lvs(self, **kwargs):
        self.calls.append(("init_lvs", kwargs))

    def run_lvs(self):
        self.calls.append(("run_lvs", {}))

    def destroy_lvs(self):
        self.calls.append(("destroy_lvs", {}))


class FakeLogger:
    def __init__(self):
        self.errors = []

    def error(self, message, *args):
        self.errors.append((message, args))


class FakeSubFlow:
    def __init__(self, **_kwargs):
        pass

    def update_step(self, **_kwargs):
        pass


def _lvs_step(tmp_path: Path, design_verilog: Path) -> EccStep:
    return EccStep(
        name=StepEnum.LVS.value,
        input=StepInput(verilog=design_verilog),
        data=EccData(dir=tmp_path / "lvs" / "data", steps={StepEnum.LVS.value: tmp_path / "lvs"}),
        feature=EccFeature(dir=tmp_path / "lvs" / "feature"),
    )


def test_run_lvs_loads_netlist_into_reused_engine(tmp_path, monkeypatch):
    design_verilog = tmp_path / "drc" / "gcd.v.gz"
    design_verilog.parent.mkdir(parents=True)
    design_verilog.write_bytes(b"gzip netlist")
    workspace = Workspace(directory=tmp_path, design=OriginDesign(name="gcd", top_module="gcd"))
    module: Any = FakeLvsModule()
    monkeypatch.setattr(ecc_runner, "EccSubFlow", FakeSubFlow)
    monkeypatch.setattr(ecc_runner, "save_data", lambda **_kwargs: True)
    monkeypatch.setattr(ecc_runner, "copy_lvs_outputs", lambda **_kwargs: True)
    monkeypatch.setattr(ecc_runner, "run_analysis", lambda **_kwargs: None)

    assert ecc_runner.run_lvs(workspace, _lvs_step(tmp_path, design_verilog), module) is True
    assert [call[0] for call in module.calls] == [
        "update_step_paths",
        "read_lvs_verilog",
        "init_lvs",
        "run_lvs",
        "destroy_lvs",
    ]
    assert module.calls[1] == ("read_lvs_verilog", str(design_verilog), "gcd")


def test_run_lvs_stops_before_native_init_when_netlist_load_fails(tmp_path, monkeypatch):
    design_verilog = tmp_path / "drc" / "gcd.v.gz"
    design_verilog.parent.mkdir(parents=True)
    design_verilog.write_bytes(b"gzip netlist")
    logger: Any = FakeLogger()
    workspace = Workspace(
        directory=tmp_path,
        design=OriginDesign(name="gcd", top_module="gcd"),
        logger=logger,
    )
    module: Any = FakeLvsModule(netlist_loaded=False)
    monkeypatch.setattr(ecc_runner, "EccSubFlow", FakeSubFlow)

    assert ecc_runner.run_lvs(workspace, _lvs_step(tmp_path, design_verilog), module) is False
    assert [call[0] for call in module.calls] == ["update_step_paths", "read_lvs_verilog"]
    assert module.calls[1] == ("read_lvs_verilog", str(design_verilog), "gcd")
    assert logger.errors == [("Failed to load LVS netlist: %s", (str(design_verilog),))]


def test_run_lvs_fails_when_no_report_was_produced(tmp_path, monkeypatch):
    """Missing ilvs.json means the LVS step failed, not a clean pass."""
    design_verilog = tmp_path / "drc" / "gcd.v.gz"
    design_verilog.parent.mkdir(parents=True)
    design_verilog.write_bytes(b"gzip netlist")
    logger: Any = FakeLogger()
    logger.info = lambda *_args: None
    workspace = Workspace(
        directory=tmp_path, design=OriginDesign(name="gcd", top_module="gcd"), logger=logger
    )
    step = _lvs_step(tmp_path, design_verilog)
    monkeypatch.setattr(ecc_runner, "EccSubFlow", FakeSubFlow)
    monkeypatch.setattr(ecc_runner, "save_data", lambda **_kwargs: True)
    monkeypatch.setattr(ecc_runner, "run_analysis", lambda **_kwargs: None)

    assert ecc_runner.run_lvs(workspace, step, FakeLvsModule()) is False
    assert logger.errors and logger.errors[0][0].startswith("LVS produced no report")


def test_copy_lvs_outputs_removes_stale_results_and_reports_fresh_ones(tmp_path):
    logger: Any = FakeLogger()
    logger.info = lambda *_args: None
    workspace = Workspace(
        directory=tmp_path, design=OriginDesign(name="gcd", top_module="gcd"), logger=logger
    )
    step = EccStep(
        name=StepEnum.LVS.value,
        input=StepInput(verilog=tmp_path / "gcd.v"),
        data=EccData(dir=tmp_path / "lvs" / "data", steps={StepEnum.LVS.value: tmp_path / "lvs"}),
        feature=EccFeature(dir=tmp_path / "lvs" / "feature", step=tmp_path / "lvs" / "f.json"),
        report=EccReport(dir=tmp_path / "lvs" / "report", step=tmp_path / "lvs" / "r.rpt"),
    )
    assert step.feature.step is not None and step.report.step is not None
    step.feature.step.parent.mkdir(parents=True, exist_ok=True)
    step.feature.step.write_text('{"violations": []}')

    assert ecc_runner.copy_lvs_outputs(workspace, step) is False
    assert not step.feature.step.exists()

    reporter = tmp_path / "lvs" / "lvs_reporter"
    reporter.mkdir(parents=True)
    (reporter / "ilvs.json").write_text('{"violations": [{"id": 1}]}')
    assert ecc_runner.copy_lvs_outputs(workspace, step) is True
    assert step.feature.step.read_text() == '{"violations": [{"id": 1}]}'


@pytest.mark.parametrize("feature", [None, {}, {"violations": None}, {"violations": "x"}])
def test_lvs_count_is_unavailable_without_a_violations_list(tmp_path, feature):
    """A missing/garbled LVS report must not read as lvs_count == 0 (clean)."""
    workspace = Workspace(directory=tmp_path, design=OriginDesign(name="gcd", top_module="gcd"))
    step = build_step(
        workspace=workspace,
        step_name=StepEnum.LVS.value,
        input_def=tmp_path / "input.def",
        input_verilog=tmp_path / "input.v",
    )
    build_step_space(step)
    assert step.feature.step is not None
    if feature is not None:
        step.feature.step.write_text(json.dumps(feature), encoding="utf-8")

    metrics = build_metrics_lvs(workspace, step)

    assert metrics is None or "lvs_count" not in metrics.data
