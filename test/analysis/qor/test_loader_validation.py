from types import SimpleNamespace
from typing import Any

import pytest

from chipcompiler.analysis.qor.dimensions import evaluate_dimensions
from chipcompiler.analysis.qor.features import compute_features
from chipcompiler.analysis.qor.loader import QorInputs, _select_metrics, load_workspace_qor_inputs
from chipcompiler.tools.ecc.metrics import _metric_scope_and_roles
from test.analysis.qor.helpers import (
    FULL_FLOW,
    loader_metric,
    make_loader_workspace,
    write_step_payload,
)


class TestMetricRangeValidation:
    @pytest.mark.parametrize("bad", [52.0, -0.3, 0.0])
    def test_out_of_range_utilization_is_unknown_with_warning(self, tmp_path, bad):
        workspace = make_loader_workspace(tmp_path, FULL_FLOW)
        write_step_payload(
            workspace.directory,
            "placement_dreamplace",
            [loader_metric("core_utilization", bad), loader_metric("place_hpwl", 10.0)],
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("core_utilization") is None
        assert inputs.value("place_hpwl") == 10.0
        assert any("core_utilization" in w and "out of range" in w for w in inputs.config_warnings)

    def test_negative_count_is_unknown(self, tmp_path):
        workspace = make_loader_workspace(tmp_path, FULL_FLOW)
        write_step_payload(workspace.directory, "routing_ecc", [loader_metric("drc_count", -1.0)])
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_count") is None
        assert any("drc_count" in w for w in inputs.config_warnings)

    def test_valid_values_and_signed_slack_are_kept(self, tmp_path):
        workspace = make_loader_workspace(tmp_path, FULL_FLOW)
        write_step_payload(
            workspace.directory,
            "placement_dreamplace",
            [
                loader_metric("core_utilization", 1.0),
                loader_metric("place_rudy_utilization_max", 1.4),
                loader_metric("sta_setup_wns", -2.5),
            ],
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("core_utilization") == 1.0
        assert inputs.value("place_rudy_utilization_max") == 1.4
        assert inputs.value("sta_setup_wns") == -2.5
        assert inputs.config_warnings == []

    @pytest.mark.parametrize("pair", [(2.0, 0.5), (0.5, 2.0)])
    def test_out_of_range_and_valid_duplicate_in_same_step_conflicts(self, pair):
        records = [
            {"id": "core_utilization", "value": pair[0], "project_role": "final"},
            {"id": "core_utilization", "value": pair[1], "project_role": "final"},
        ]
        warnings: list[str] = []
        selected = _select_metrics([("post_floorplan", records)], warnings)
        assert "core_utilization" not in selected
        assert any("out of range" in w for w in warnings)
        assert any("conflicting" in w for w in warnings)

    def test_identical_out_of_range_duplicates_emit_single_range_warning(self):
        records = [
            {"id": "core_utilization", "value": 2.0, "project_role": "final"},
            {"id": "core_utilization", "value": 2.0, "project_role": "final"},
        ]
        warnings: list[str] = []
        selected = _select_metrics([("post_floorplan", records)], warnings)
        assert "core_utilization" not in selected
        assert len(warnings) == 1
        assert "out of range" in warnings[0]

    def test_out_of_range_authoritative_record_overrides_earlier_trend(self):
        payloads = []
        for step, value in [("post_floorplan", 0.5), ("routing", 1.5)]:
            _, role, _ = _metric_scope_and_roles(SimpleNamespace(name=step), "core_utilization")
            payloads.append(
                (step, [{"id": "core_utilization", "value": value, "project_role": role}])
            )

        warnings: list[str] = []
        selected = _select_metrics(payloads, warnings)
        inputs = QorInputs(metrics=selected)
        area = evaluate_dimensions(compute_features(inputs), inputs)["area"]

        assert "core_utilization" not in selected
        assert area.value is None
        assert area.state == "UNKNOWN"
        assert any("core_utilization=1.5" in w and "out of range" in w for w in warnings)

    def test_valid_authoritative_record_overrides_earlier_out_of_range_trend(self):
        payloads = []
        for step, value in [("post_floorplan", 1.5), ("routing", 0.5)]:
            _, role, _ = _metric_scope_and_roles(SimpleNamespace(name=step), "core_utilization")
            payloads.append(
                (step, [{"id": "core_utilization", "value": value, "project_role": role}])
            )

        warnings: list[str] = []
        selected = _select_metrics(payloads, warnings)

        assert selected["core_utilization"].value == 0.5
        assert selected["core_utilization"].step == "routing"
        assert any("core_utilization=1.5" in w and "out of range" in w for w in warnings)
