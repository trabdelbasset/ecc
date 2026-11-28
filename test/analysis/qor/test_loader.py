import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from chipcompiler.analysis.qor.loader import load_workspace_qor_inputs
from test.analysis.qor.helpers import (
    FULL_FLOW as _FULL_FLOW,
)
from test.analysis.qor.helpers import (
    SUCCESS,
)
from test.analysis.qor.helpers import (
    loader_metric as _metric,
)
from test.analysis.qor.helpers import (
    make_loader_workspace as _make_workspace,
)
from test.analysis.qor.helpers import (
    write_json as _write,
)
from test.analysis.qor.helpers import (
    write_step_payload as _write_step_payload,
)


class TestMetricSelection:
    def test_role_priority_final_beats_trend(self, tmp_path):
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        _write_step_payload(
            workspace.directory,
            "place_ecc".replace("place_ecc", "placement_dreamplace"),
            [_metric("place_hpwl", 100.0, project_role="trend")],
        )
        _write_step_payload(
            workspace.directory,
            "routing_ecc",
            [_metric("place_hpwl", 200.0, project_role="final")],
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("place_hpwl") == 200.0

    def test_later_step_wins_within_same_role(self, tmp_path):
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        _write_step_payload(
            workspace.directory,
            "placement_dreamplace",
            [_metric("place_hpwl", 100.0, project_role="trend")],
        )
        _write_step_payload(
            workspace.directory,
            "routing_ecc",
            [_metric("place_hpwl", 111.0, project_role="trend")],
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("place_hpwl") == 111.0
        assert inputs.metrics["place_hpwl"].step == "routing"

    def test_conflicting_duplicate_record_is_unknown_and_warned(self, tmp_path):
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        _write_step_payload(
            workspace.directory,
            "drc_ecc",
            [_metric("drc_count", 0.0), _metric("drc_count", 999.0)],
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_count") is None
        assert any("drc_count" in w and "conflicting" in w for w in inputs.config_warnings)

    def test_identical_duplicate_record_is_harmless(self, tmp_path):
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        _write_step_payload(
            workspace.directory,
            "drc_ecc",
            [_metric("drc_count", 0.0), _metric("drc_count", 0.0)],
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_count") == 0.0
        assert inputs.config_warnings == []

    def test_better_role_record_overrides_conflicting_duplicates(self, tmp_path):
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        _write_step_payload(
            workspace.directory,
            "placement_dreamplace",
            [
                _metric("place_hpwl", 1.0, project_role="trend"),
                _metric("place_hpwl", 2.0, project_role="trend"),
            ],
        )
        _write_step_payload(
            workspace.directory,
            "routing_ecc",
            [_metric("place_hpwl", 200.0, project_role="final")],
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("place_hpwl") == 200.0
        assert inputs.config_warnings == []

    def test_same_step_cross_role_conflict_is_unknown(self, tmp_path):
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        _write_step_payload(
            workspace.directory,
            "drc_ecc",
            [
                _metric("drc_count", 0.0, project_role="gate"),
                _metric("drc_count", 2.0, project_role="trend"),
            ],
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_count") is None
        assert any("conflicting" in w for w in inputs.config_warnings)

    @pytest.mark.parametrize("pair", [(0, False), (False, 0)])
    def test_bool_vs_int_duplicate_is_conflicted_in_both_readers(self, tmp_path, pair):
        from chipcompiler.tools.ecc.qor_metrics import QorMetrics

        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        _write_step_payload(
            workspace.directory,
            "drc_ecc",
            [_metric("drc_count", pair[0]), _metric("drc_count", pair[1])],
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_count") is None
        assert any("conflicting" in w for w in inputs.config_warnings)

        qor_path = Path(workspace.directory) / "drc_ecc" / "analysis" / "qor_metrics.json"
        value, error = QorMetrics(qor_path).number("drc_count")
        assert value is None
        assert error == "qor_metrics.json contains conflicting duplicate metric id drc_count"

    def test_int_and_equal_float_duplicate_accepted_in_both_readers(self, tmp_path):
        from chipcompiler.tools.ecc.qor_metrics import QorMetrics

        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        _write_step_payload(
            workspace.directory,
            "drc_ecc",
            [_metric("drc_count", 0), _metric("drc_count", 0.0)],
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_count") == 0.0
        assert inputs.config_warnings == []

        qor_path = Path(workspace.directory) / "drc_ecc" / "analysis" / "qor_metrics.json"
        assert QorMetrics(qor_path).number("drc_count") == (0.0, None)

    def test_stale_payload_of_unstarted_step_is_ignored(self, tmp_path):
        steps = dict(_FULL_FLOW)
        steps["routing"] = "Unstart"
        workspace = _make_workspace(tmp_path, steps)
        _write_step_payload(
            workspace.directory, "routing_ecc", [_metric("route_wirelength", 9999.0)]
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("route_wirelength") is None
        assert "routing" not in inputs.analyzed_steps
        assert inputs.parse_failures == 0  # unstarted steps are not failures

    def test_step_skipped_from_the_ledger_contributes_nothing(self, tmp_path):
        steps = {name: state for name, state in _FULL_FLOW.items() if name != "cts"}
        workspace = _make_workspace(tmp_path, steps)
        _write_step_payload(workspace.directory, "cts_ecc", [_metric("cts_skew", 9999.0)])
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("cts_skew") is None
        assert "cts" not in inputs.analyzed_steps
        assert inputs.parse_failures == 0

    def test_failed_payload_counts_as_parse_failure(self, tmp_path):
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        _write(
            os.path.join(workspace.directory, "drc_ecc", "analysis", "qor_metrics.json"),
            {"broken": True},
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.parse_failures == 1
        assert "drc" not in inputs.analyzed_steps


class TestParameterResolution:
    def test_frequency_max_resolves_tclk(self, tmp_path):
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.tclk_ns == pytest.approx(20.0)
        assert inputs.config_warnings == []

    def test_unknown_profile_warns_and_falls_back(self, tmp_path):
        from chipcompiler.data.workspace.config import load_workspace_config, save_workspace_config

        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        parameters = load_workspace_config(workspace.directory)
        parameters.update(frequency_max=50.0, qor_profile="speed_demon")
        assert save_workspace_config(workspace.directory, parameters)
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.profile == "balanced"
        assert inputs.config_warnings

    def test_nonpositive_budget_warns_and_undeclares(self, tmp_path):
        from chipcompiler.data.workspace.config import load_workspace_config, save_workspace_config

        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        parameters = load_workspace_config(workspace.directory)
        parameters.update(frequency_max=50.0, qor_power_budget_w=-1)
        assert save_workspace_config(workspace.directory, parameters)
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.power_budget_uw is None
        assert inputs.config_warnings

    def test_infinite_budget_warns_and_undeclares(self, tmp_path):
        from chipcompiler.data.workspace.config import load_workspace_config, save_workspace_config

        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        parameters = load_workspace_config(workspace.directory)
        parameters.update(frequency_max=50.0, qor_power_budget_w=float("inf"))
        save_workspace_config(workspace.directory, parameters)
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.power_budget_uw is None
        assert inputs.config_warnings

    def test_nonfinite_frequency_max_warns(self, tmp_path):
        from chipcompiler.data.workspace.config import load_workspace_config, save_workspace_config

        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        parameters = load_workspace_config(workspace.directory)
        parameters.update(frequency_max=float("inf"))
        save_workspace_config(workspace.directory, parameters)
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.tclk_ns is None
        assert any("frequency_max" in w for w in inputs.config_warnings)


class TestCornerLoading:
    def test_per_corner_summaries_are_parsed(self, tmp_path):
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        for corner_dir, wns in (("MAX_125_t125", 16.622), ("MAX_M40_tm40", 18.98)):
            _write(
                os.path.join(
                    workspace.directory,
                    "sta_ecc",
                    "feature",
                    corner_dir,
                    "Cworst",
                    "qor_summary.json",
                ),
                {
                    "path_groups": [],
                    "summary": {
                        "setup": {"wns": wns, "tns": 0.0, "nvp": 0, "frequency_mhz": 296.0},
                        "hold": {"wns": 0.1, "tns": 0.0, "nvp": 0},
                    },
                },
            )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert [corner.setup_ws for corner in inputs.corners] == [16.622, 18.98]

    def test_failed_sta_does_not_load_stale_corner_files(self, tmp_path):
        steps = dict(_FULL_FLOW)
        steps["sta"] = "Incomplete"
        workspace = _make_workspace(tmp_path, steps)
        _write(
            os.path.join(
                workspace.directory,
                "sta_ecc",
                "feature",
                "MAX_125_t125",
                "Cworst",
                "qor_summary.json",
            ),
            {
                "path_groups": [],
                "summary": {
                    "setup": {"wns": 1.0, "tns": 0.0, "nvp": 0, "frequency_mhz": 50.0},
                    "hold": {"wns": 1.0, "tns": 0.0, "nvp": 0},
                },
            },
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.corners == []

    def test_synthesis_power_summary_is_loaded(self, tmp_path):
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        _write(
            os.path.join(
                workspace.directory,
                "synthesis_yosys",
                "feature",
                "post_synthesis",
                "power_summary.json",
            ),
            {
                "schema_version": 1,
                "dynamic_uw": 3.0,
                "leakage_uw": 4.0,
                "internal_uw": 1.0,
                "switching_uw": 2.0,
            },
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.power_total_uw == 7.0
        assert inputs.power_source_path.endswith(
            "synthesis_yosys/feature/post_synthesis/power_summary.json"
        )
        assert inputs.power_source_kind == "synthesis"
        assert inputs.power_corner == "post_synthesis"

    def test_signoff_power_uses_worst_configured_corner(self, tmp_path):
        workspace = _make_workspace(tmp_path, {**_FULL_FLOW, "power_analysis": SUCCESS})
        _write(
            os.path.join(
                workspace.directory,
                "power_analysis_ecc",
                "feature",
                "power_analysis.step.json",
            ),
            {
                "schema_version": 1,
                "step": "power_analysis",
                "power_summary": {
                    "schema_version": 1,
                    "dynamic_uw": 8.0,
                    "leakage_uw": 1.0,
                    "internal_uw": 2.0,
                    "switching_uw": 6.0,
                },
            },
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.power_total_uw == 9.0
        assert inputs.power_source_path.endswith(
            "power_analysis_ecc/feature/power_analysis.step.json"
        )
        assert inputs.power_source_kind == "signoff"
        assert inputs.power_corner == "power_analysis"

    def test_power_analysis_summary_replaces_sta_power_source(self, tmp_path):
        steps = {**_FULL_FLOW, "power_analysis": SUCCESS}
        workspace = _make_workspace(tmp_path, steps)
        _write(
            os.path.join(
                workspace.directory,
                "power_analysis_ecc",
                "feature",
                "power_analysis.step.json",
            ),
            {
                "schema_version": 1,
                "step": "power_analysis",
                "power_summary": {
                    "schema_version": 1,
                    "dynamic_uw": 8.0,
                    "leakage_uw": 1.0,
                    "internal_uw": 2.0,
                    "switching_uw": 6.0,
                },
            },
        )
        # A current workspace must not fall back to the old STA location.
        _write(
            os.path.join(
                workspace.directory,
                "sta_ecc",
                "feature",
                "MAX_125",
                "Cworst",
                "power_summary.json",
            ),
            {
                "schema_version": 1,
                "dynamic_uw": 90.0,
                "leakage_uw": 10.0,
                "internal_uw": 20.0,
                "switching_uw": 70.0,
            },
        )

        inputs: Any = load_workspace_qor_inputs(workspace)

        assert inputs.power_total_uw == 9.0
        assert inputs.power_source_path.endswith(
            "power_analysis_ecc/feature/power_analysis.step.json"
        )
        assert inputs.power_source_kind == "signoff"
        assert inputs.power_corner == "power_analysis"

    def test_incomplete_power_analysis_does_not_score_stale_power_summary(self, tmp_path):
        steps = {**_FULL_FLOW, "power_analysis": "Incomplete"}
        workspace = _make_workspace(tmp_path, steps)
        _write(
            os.path.join(
                workspace.directory,
                "power_analysis_ecc",
                "feature",
                "power_summary.json",
            ),
            {
                "schema_version": 1,
                "dynamic_uw": 8.0,
                "leakage_uw": 1.0,
                "internal_uw": 2.0,
                "switching_uw": 6.0,
            },
        )

        inputs: Any = load_workspace_qor_inputs(workspace)

        assert inputs.power_total_uw is None

    def test_setup_only_corner_is_loaded_with_fallback_marker(self, tmp_path):
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        _write(
            os.path.join(
                workspace.directory,
                "sta_ecc",
                "feature",
                "MAX_125_t125",
                "Cworst",
                "qor_summary.json",
            ),
            {
                "path_groups": [],
                "summary": {"setup": {"wns": 1.0, "tns": 0.0, "nvp": 0}},
            },
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert len(inputs.corners) == 1
        assert inputs.sta_setup_only is True

    def test_corner_with_float_violation_count_is_not_loaded(self, tmp_path):
        # An unparseable corner must be absent (never silently coerced) so the
        # gates see fewer loaded corners than expected and report UNKNOWN.
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        _write(
            os.path.join(
                workspace.directory,
                "sta_ecc",
                "feature",
                "MAX_125_t125",
                "Cworst",
                "qor_summary.json",
            ),
            {
                "path_groups": [],
                "summary": {
                    "setup": {"wns": -0.5, "tns": 0.0, "nvp": 3.5, "frequency_mhz": 296.0},
                    "hold": {"wns": 0.1, "tns": 0.0, "nvp": 0},
                },
            },
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.corners == []


class TestDesignResolution:
    def test_design_falls_back_to_parameters(self, tmp_path):
        workspace = _make_workspace(tmp_path, _FULL_FLOW)
        workspace.design = SimpleNamespace(name="")
        workspace.name = ""
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.design == "gcd"


def _index_step_directories(root: Path) -> None:
    """Move each step directory to its indexed name and record it in the ledger."""
    from chipcompiler.data.step import STEP_DIRECTORIES

    flow_path = root / "home" / "flow.json"
    flow = json.loads(flow_path.read_text(encoding="utf-8"))
    for index, record in enumerate(flow["steps"], start=1):
        legacy = STEP_DIRECTORIES[record["name"]]
        record["directory"] = f"{index:02d}_{legacy}"
        if (root / legacy).is_dir():
            (root / legacy).rename(root / record["directory"])
    flow_path.write_text(json.dumps(flow), encoding="utf-8")


def test_indexed_step_directories_score_like_the_legacy_layout(tmp_path):
    from chipcompiler.analysis.qor import build_qor_analysis
    from test.analysis.qor.test_reference_gcd import _make_gcd_workspace

    legacy = build_qor_analysis(_make_gcd_workspace(tmp_path / "legacy"))
    workspace = _make_gcd_workspace(tmp_path / "indexed")
    _index_step_directories(Path(workspace.directory))

    indexed = build_qor_analysis(workspace)

    assert (indexed.feasibility, indexed.qor_record, indexed.scalar_summary) == (
        legacy.feasibility,
        legacy.qor_record,
        legacy.scalar_summary,
    )
    assert indexed.evidence == legacy.evidence
