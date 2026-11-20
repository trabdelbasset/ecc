import json
from typing import Any

import pytest

from chipcompiler.data import EccFeature, EccReport, EccStep, OriginDesign, StepEnum, Workspace
from chipcompiler.tools.ecc.antenna_coverage import antenna_coverage, read_antenna_check
from chipcompiler.tools.ecc.signoff_checklist import _step_artifact_items


@pytest.mark.parametrize(
    ("block", "verified"),
    [
        ({"signal_net_count": 4213, "pins_with_gate_area": 9781, "violation_count": 0}, True),
        ({"signal_net_count": 0, "pins_with_gate_area": 0, "violation_count": 0}, False),
        ({"signal_net_count": 10, "pins_with_gate_area": 0}, False),
        ({"signal_net_count": 0, "pins_with_gate_area": 5}, False),
        ({"violation_count": 0}, False),
        (None, False),
    ],
)
def test_antenna_coverage(block, verified):
    ok, message = antenna_coverage(block)
    assert ok is verified
    assert message


def test_zero_net_message_names_both_causes():
    _, message = antenna_coverage({"signal_net_count": 0, "pins_with_gate_area": 0})
    assert "0 nets" in message and "ANTENNAGATEAREA" in message


def _antenna_step(tmp_path, step_json: dict | None) -> Any:
    root = tmp_path / "antenna_check_ecc"
    step: Any = EccStep(
        name=StepEnum.ANTENNA_CHECK.value,
        directory=root,
        feature=EccFeature(dir=root / "feature", step=root / "feature" / "antenna_check.step.json"),
        report=EccReport(dir=root / "report", step=root / "report" / "antenna_check.rpt"),
    )
    step.report.step.parent.mkdir(parents=True)
    step.report.step.write_text("Total Violations: 0\n", encoding="utf-8")
    if step_json is not None:
        step.feature.dir.mkdir(parents=True)
        step.feature.step.write_text(json.dumps(step_json), encoding="utf-8")
    return step


def _coverage_item(tmp_path, step_json):
    workspace = Workspace(directory=tmp_path, design=OriginDesign(name="gcd"))
    step = _antenna_step(tmp_path, step_json)
    items = {item["id"]: item for item in _step_artifact_items(workspace, step)}
    return items["quality.antenna.coverage"], items["artifact.antenna_check.report"]


def test_vacuous_antenna_check_is_a_warning_not_a_pass(tmp_path):
    block = {"signal_net_count": 0, "pins_with_gate_area": 0, "violation_count": 0}
    item, report = _coverage_item(tmp_path, {"antenna_check": block})
    assert item["state"] == "warning"
    assert item["policy"] == "warn"
    assert item["blocked"] is False
    assert "not verified" in item["summary"]
    assert report["state"] == "pass"  # report presence is a separate artifact check


def test_missing_step_json_is_a_warning(tmp_path):
    item, _ = _coverage_item(tmp_path, None)
    assert item["state"] == "warning"


def test_analysed_antenna_check_passes_coverage(tmp_path):
    block = {"signal_net_count": 12, "pins_with_gate_area": 30, "violation_count": 0}
    item, _ = _coverage_item(tmp_path, {"antenna_check": block})
    assert item["state"] == "pass"
    step_json = tmp_path / "antenna_check_ecc" / "feature" / "antenna_check.step.json"
    assert read_antenna_check(step_json) == block


def test_antenna_diagnostics_warn_on_dropped_geometry(tmp_path):
    block = {
        "signal_net_count": 12,
        "pins_with_gate_area": 30,
        "violation_count": 0,
        "skipped_segments": 2,
        "conductors_out_of_range": 1,
        "partial_areas_dropped": 3,
    }
    ok, message = antenna_coverage(block)
    assert ok is True
    assert "skipped_segments=2" in message
    assert "conductors_out_of_range=1" in message
    assert "partial_areas_dropped=3" in message

    item, _ = _coverage_item(tmp_path, {"antenna_check": block})
    assert item["state"] == "warning"
    assert "skipped_segments=2" in item["summary"]
