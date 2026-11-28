"""Shared fixtures for the QoR engine tests."""

import json
import os
from types import SimpleNamespace

from chipcompiler.analysis.qor.loader import CornerSlack, MetricRecord, QorInputs
from test.flow_fixture import step_fields

SUCCESS = "Success"

STEP_TOOLS = {"synthesis": "yosys", "placement": "dreamplace"}

STEP_DIRECTORIES = {
    "synthesis": "synthesis_yosys",
    "post_floorplan": "post_floorplan_ecc",
    "placement": "placement_dreamplace",
    "cts": "cts_ecc",
    "routing": "routing_ecc",
    "drc": "drc_ecc",
    "lvs": "lvs_ecc",
    "rcx": "rcx_ecc",
    "sta": "sta_ecc",
    "power_analysis": "power_analysis_ecc",
    "harden": "harden_ecc",
}

FULL_FLOW = {
    "synthesis": SUCCESS,
    "post_floorplan": SUCCESS,
    "placement": SUCCESS,
    "cts": SUCCESS,
    "routing": SUCCESS,
    "drc": SUCCESS,
    "lvs": SUCCESS,
    "rcx": SUCCESS,
    "sta": SUCCESS,
    "harden": SUCCESS,
}


def touch_qor_evidence(path, payload):
    """Create each metric's evidence artifact (older than the cache written next)."""
    if not isinstance(payload, dict):
        return
    step_dir = os.path.dirname(os.path.dirname(str(path)))
    for metric in payload.get("metrics", []):
        source = metric.get("source")
        rel = source.get("path") if isinstance(source, dict) else None
        if not isinstance(rel, str) or not rel or os.path.isabs(rel):
            continue
        os.makedirs(os.path.dirname(os.path.join(step_dir, rel)), exist_ok=True)
        with open(os.path.join(step_dir, rel), "a"):
            pass


def make_metric(metric_id, value, step="sta", role="final", unit="", corner=None):
    return MetricRecord(
        metric_id=metric_id,
        value=value,
        unit=unit,
        step=step,
        project_role=role,
        corner=corner,
        source={"kind": "analysis", "path": f"{step}_ecc/analysis/qor_metrics.json"},
        scope="project",
    )


def make_inputs(metrics=None, flow_states=None, **overrides) -> QorInputs:
    metrics = metrics or {}

    def _value(metric_id):
        return metrics[metric_id].value if metric_id in metrics else None

    derived = {
        # Mirror the loader: corner/SPEF counts come from payload metrics.
        "sta_expected_corners": _value("sta_expected_corner_count"),
        "rcx_spef_count": _value("rcx_spef_file_count"),
        "rcx_expected_spef": _value("rcx_expected_corner_count"),
    }
    derived.update(overrides)
    inputs = QorInputs(
        design="gcd",
        workspace_path="/tmp/ws",
        flow_states=flow_states if flow_states is not None else _all_success(),
        metrics=metrics,
    )
    for key, value in derived.items():
        setattr(inputs, key, value)
    return inputs


def _all_success():
    return {
        step: SUCCESS
        for step in (
            "synthesis",
            "post_floorplan",
            "placement",
            "cts",
            "routing",
            "drc",
            "lvs",
            "rcx",
            "sta",
            "harden",
        )
    }


def gcd_metrics() -> dict:
    """Reference GCD fixture inputs (spec §12.1)."""
    records = [
        make_metric("synthesis_cell_area", 800.0, step="synthesis"),
        make_metric("core_area", 1538.46, step="post_floorplan"),
        make_metric("core_utilization", 0.52, step="post_floorplan"),
        make_metric("place_hpwl", 3143.52, step="placement"),
        make_metric("place_grwl", 3812.00, step="placement"),
        make_metric("place_rudy_utilization_max", 0.0, step="placement"),
        make_metric("cts_buffer_count", 4, step="cts"),
        make_metric("cts_inverter_count", 0, step="cts"),
        make_metric("clock_path_max_buffer", 4, step="cts"),
        make_metric("clock_path_min_buffer", 4, step="cts"),
        make_metric("clock_wirelength", 610.0, step="cts"),
        make_metric("route_wirelength", 4315.53, step="routing"),
        make_metric("route_via_count", 608, step="routing"),
        make_metric("drc_count", 0, step="drc"),
        make_metric("lvs_count", 0, step="lvs"),
        make_metric("rcx_spef_file_count", 2, step="rcx"),
        make_metric("rcx_expected_corner_count", 2, step="rcx"),
        make_metric("rcx_missing_corner_count", 0, step="rcx"),
        make_metric("rcx_worst_total_capacitance_ff", 120.0, step="rcx"),
        make_metric("rcx_worst_coupling_capacitance_ff", 30.0, step="rcx"),
        make_metric("sta_setup_wns", 16.622, step="sta"),
        make_metric("sta_setup_tns", 0.0, step="sta"),
        make_metric("sta_hold_wns", 0.1, step="sta"),
        make_metric("sta_hold_tns", 0.0, step="sta"),
        make_metric("sta_setup_violation_count", 0, step="sta"),
        make_metric("sta_hold_violation_count", 0, step="sta"),
        make_metric("sta_max_transition_violation_count", 0, step="sta"),
        make_metric("sta_max_capacitance_violation_count", 0, step="sta"),
        make_metric("sta_max_fanout_violation_count", 0, step="sta"),
        make_metric("sta_expected_corner_count", 2, step="sta"),
        make_metric("sta_missing_corner_count", 0, step="sta"),
        make_metric("sta_worst_setup_corner", "MAX_125", step="sta"),
        make_metric("harden_artifact_missing_count", 0, step="harden"),
    ]
    return {record.metric_id: record for record in records}


def gcd_corners():
    """Two corners reproducing the spec §12.1 dispersions.

    WS spread: 18.980 - 16.622 = 2.358 ns; hold spread: 0.274 - 0.100 = 0.174 ns.
    """
    return [
        CornerSlack(corner="MAX_125", setup_ws=16.622, hold_ws=0.100, setup_nvp=0, hold_nvp=0),
        CornerSlack(corner="MAX_M40", setup_ws=18.980, hold_ws=0.274, setup_nvp=0, hold_nvp=0),
    ]


def write_json(path, payload):
    if str(path).endswith("qor_metrics.json"):
        touch_qor_evidence(path, payload)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f)


def loader_metric(metric_id, value, project_role="final", **overrides):
    record = {
        "id": metric_id,
        "display_name": metric_id,
        "value": value,
        "unit": "",
        "category": "timing",
        "direction": "lower_is_better",
        "scope": "project",
        "corner": None,
        "project_role": project_role,
        "step_role": "primary",
        "rating": {"gate": False, "score": True, "trend": True},
        "source": {"kind": "analysis", "path": "feature/x.json"},
    }
    record.update(overrides)
    return record


def loader_payload(metrics, details=None):
    payload = {
        "schema_version": 3,
        "kind": "qor_metrics",
        "integrity": {"status": "pass", "invalid_metric_source_ids": [], "invalid_detail_ids": []},
        "metrics": metrics,
    }
    if details is not None:
        payload["details"] = details
    return payload


def write_step_payload(root, directory, metrics, details=None):
    write_json(
        os.path.join(root, directory, "analysis", "qor_metrics.json"),
        loader_payload(metrics, details=details),
    )


def make_loader_workspace(tmp_path, steps):
    root = str(tmp_path / "ws")
    write_json(
        os.path.join(root, "home", "flow.json"),
        {
            "schema_version": 3,
            "steps": [
                {
                    "name": name,
                    "tool": STEP_TOOLS.get(name, "ecc"),
                    "state": state,
                    **step_fields(name, STEP_TOOLS.get(name, "ecc")),
                }
                for name, state in steps.items()
            ],
        },
    )
    from chipcompiler.data.workspace.config import save_workspace_config

    assert save_workspace_config(root, {"design": "gcd", "frequency_max": 50.0})
    # Every successful step emits a minimal valid payload unless a test
    # overwrites it; the loader treats a missing payload as a parse failure.
    for step_value, state in steps.items():
        if state == SUCCESS:
            write_step_payload(
                root, STEP_DIRECTORIES[step_value], [loader_metric("probe_metric", 1.0)]
            )

    class _Flow:
        data = {}

    return SimpleNamespace(
        directory=root, name="gcd", design=SimpleNamespace(name="gcd"), flow=_Flow()
    )
