#!/usr/bin/env python
from collections.abc import Callable
from math import isfinite
from pathlib import Path

from chipcompiler.analysis.qor.gate_catalog import step_gate_blocking
from chipcompiler.data import StateEnum, StepEnum, Workspace, WorkspaceStep
from chipcompiler.data.step import recorded_step_directory
from chipcompiler.utility import json_read

# Design-rule violation counts summed over the configured signoff corners.
STA_DRV_METRIC_IDS = (
    "sta_max_transition_violation_count",
    "sta_max_capacitance_violation_count",
    "sta_max_fanout_violation_count",
)

MetricLookup = Callable[[str], tuple[int | float | None, dict | None]]


def qor_number(value) -> int | float | None:
    """Parse a finite numeric metric value, normalizing percentage strings."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if text == "":
            return None
        percent = text.endswith("%")
        if percent:
            text = text[:-1].strip()
        text = text.replace(",", "")
        try:
            number = float(text)
        except ValueError:
            return None
        if percent:
            number = number / 100.0
    else:
        return None

    if not isfinite(number):
        return None
    return int(number) if number.is_integer() else number


def is_feature_source(source) -> bool:
    """Return True if *source* is a step-local ``feature/`` evidence pointer."""
    if not isinstance(source, dict) or source.get("kind") != "feature":
        return False
    path = source.get("path")
    selector = source.get("selector")
    return (
        isinstance(path, str)
        and path.startswith("feature/")
        and ".." not in Path(path).parts
        and isinstance(selector, str)
        and (selector == "" or selector.startswith("/"))
    )


def _quality_gate(
    gate_id: str,
    title: str,
    state: str,
    metrics: list[dict],
    evidence: list[dict],
    *,
    blocking: bool | None = None,
) -> dict:
    return {
        "id": gate_id,
        "title": title,
        "state": state,
        "blocking": step_gate_blocking(gate_id) if blocking is None else blocking,
        "metrics": metrics,
        "evidence": evidence,
    }


def _quality_gate_metric(
    metric_id: str,
    actual,
    operator: str,
    expected,
    source: dict | None = None,
) -> dict:
    metric = {
        "id": metric_id,
        "actual": actual,
        "operator": operator,
        "expected": expected,
    }
    if _is_quality_gate_feature_source(source):
        metric["source"] = source
    return metric


def _is_quality_gate_feature_source(source) -> bool:
    if is_feature_source(source):
        return True
    if not isinstance(source, dict) or source.get("kind") != "feature":
        return False
    path = source.get("path")
    selector = source.get("selector")
    if not isinstance(path, str) or not isinstance(selector, str):
        return False
    path_parts = Path(path).parts
    return (
        not Path(path).is_absolute()
        and ".." not in path_parts
        and len(path_parts) >= 3
        and path_parts[1] == "feature"
        and (selector == "" or selector.startswith("/"))
    )


def _quality_gate_evidence(*sources: dict | None) -> list[dict]:
    evidence = []
    seen = set()
    for source in sources:
        if not isinstance(source, dict) or not _is_quality_gate_feature_source(source):
            continue
        key = (source.get("kind"), source.get("path"), source.get("selector"))
        if key in seen:
            continue
        seen.add(key)
        evidence.append(source)
    return evidence


def _gate_state(*, available: bool, passed: bool) -> str:
    if not available:
        return "unavailable"
    return "pass" if passed else "failed"


_MPC_AREA_SOURCE_STEPS = {
    StepEnum.POST_FLOORPLAN.value,
    StepEnum.PLACEMENT.value,
    StepEnum.CTS.value,
    StepEnum.LEGALIZATION.value,
    StepEnum.ROUTING.value,
}


def _mpc_area_bound(value) -> float | None:
    number = qor_number(value)
    return number if number is not None and number > 0 else None


def _mpc_area_constraints(workspace: Workspace | None) -> tuple[float | None, float | None] | None:
    parameters = getattr(getattr(workspace, "parameters", None), "data", {})
    if not isinstance(parameters, dict):
        return None
    mpc = parameters.get("mpc")
    core_template = mpc.get("core_template") if isinstance(mpc, dict) else None
    if not isinstance(core_template, dict):
        return None
    return (
        _mpc_area_bound(core_template.get("minimum_area")),
        _mpc_area_bound(core_template.get("maximum_area")),
    )


def _last_successful_mpc_area_source(workspace: Workspace) -> tuple[float | None, dict | None]:
    """Return the latest successful physical DB at or before routing.

    Signoff steps intentionally never provide MPC die-area evidence: their data
    is signoff output rather than the physical implementation checkpoint.
    """
    flow_data = getattr(getattr(workspace, "flow", None), "data", {})
    flow_steps = flow_data.get("steps", []) if isinstance(flow_data, dict) else []
    candidates = [
        item
        for item in flow_steps
        if isinstance(item, dict)
        and item.get("name") in _MPC_AREA_SOURCE_STEPS
        and item.get("state") == StateEnum.Success.value
    ]
    if not candidates:
        return None, None

    flow_step = candidates[-1]
    step_name = str(flow_step.get("name"))
    feature_path = (
        Path(workspace.directory)
        / recorded_step_directory(flow_step)
        / "feature"
        / f"{step_name}.db.json"
    )
    relative_path = _relative_workspace_path(workspace, feature_path)
    source = {
        "kind": "feature",
        "path": relative_path,
        "selector": "/Design Layout/die_area",
    }
    data = json_read(feature_path)
    layout = data.get("Design Layout") if isinstance(data, dict) else None
    area = qor_number(layout.get("die_area")) if isinstance(layout, dict) else None
    return area, source


def _relative_workspace_path(workspace: Workspace, path: Path) -> str:
    workspace_directory = workspace.directory
    try:
        return path.relative_to(workspace_directory).as_posix()
    except ValueError:
        return str(path)


def _mpc_area_gates(workspace: Workspace | None) -> list[dict]:
    constraints = _mpc_area_constraints(workspace)
    if constraints is None:
        return []

    minimum_area, maximum_area = constraints
    actual_area, source = (
        _last_successful_mpc_area_source(workspace) if workspace is not None else (None, None)
    )
    constraints_valid = (
        minimum_area is not None and maximum_area is not None and minimum_area <= maximum_area
    )
    available = constraints_valid and actual_area is not None
    minimum_area_passed = False
    maximum_area_passed = False
    if available:
        assert actual_area is not None
        assert minimum_area is not None
        assert maximum_area is not None
        minimum_area_passed = actual_area >= minimum_area
        maximum_area_passed = actual_area <= maximum_area
    return [
        _quality_gate(
            "qor.mpc.minimum_area",
            "MPC minimum die area",
            _gate_state(available=available, passed=minimum_area_passed),
            [_quality_gate_metric("minimum_area", actual_area, ">=", minimum_area, source)],
            _quality_gate_evidence(source),
        ),
        _quality_gate(
            "qor.mpc.maximum_area",
            "MPC maximum die area",
            _gate_state(available=available, passed=maximum_area_passed),
            [_quality_gate_metric("maximum_area", actual_area, "<=", maximum_area, source)],
            _quality_gate_evidence(source),
        ),
    ]


def _zero_count_gate(gate_id: str, title: str, metric_id: str, metric: MetricLookup) -> list[dict]:
    count, source = metric(metric_id)
    return [
        _quality_gate(
            gate_id,
            title,
            _gate_state(available=count is not None, passed=count == 0),
            [_quality_gate_metric(metric_id, count, "==", 0, source)],
            _quality_gate_evidence(source),
        )
    ]


def _drc_gates(metric: MetricLookup) -> list[dict]:
    return _zero_count_gate("qor.drc.clean", "Final DRC clean", "drc_count", metric)


def _lvs_gates(metric: MetricLookup) -> list[dict]:
    return _zero_count_gate("qor.lvs.clean", "Final LVS clean", "lvs_count", metric)


def _antenna_gates(metric: MetricLookup) -> list[dict]:
    count, source = metric("antenna_violation_count")
    nets, nets_source = metric("antenna_signal_net_count")
    pins, pins_source = metric("antenna_gate_pin_count")
    # Zero nets or gate pins analysed means the check was vacuous: not verified, never clean.
    covered = nets is not None and nets > 0 and pins is not None and pins > 0
    violated = count is not None and count > 0
    return [
        _quality_gate(
            "qor.antenna.clean",
            "Antenna violations (analysed)",
            _gate_state(
                available=violated or (count is not None and covered),
                passed=covered and count == 0,
            ),
            [
                _quality_gate_metric("antenna_violation_count", count, "==", 0, source),
                _quality_gate_metric("antenna_signal_net_count", nets, ">", 0, nets_source),
                _quality_gate_metric("antenna_gate_pin_count", pins, ">", 0, pins_source),
            ],
            _quality_gate_evidence(source, nets_source, pins_source),
        )
    ]


def _rcx_gates(feature: dict, metric: MetricLookup) -> list[dict]:
    signoff = feature.get("rcx", {}).get("signoff_metrics", {})
    coverage = signoff.get("coverage", {}) if isinstance(signoff, dict) else {}
    expected, expected_source = metric("rcx_expected_corner_count")
    available, available_source = metric("rcx_spef_file_count")
    missing, missing_source = metric("rcx_missing_corner_count")
    parse_failures, parse_source = metric("rcx_spef_parse_failure_count")
    coverage_available = (
        isinstance(coverage, dict)
        and expected is not None
        and available is not None
        and missing is not None
        and expected > 0
    )
    coverage_passed = (
        coverage_available
        and coverage.get("status") == "pass"
        and available == expected
        and missing == 0
    )
    parse_available = coverage_available and parse_failures is not None
    parse_passed = parse_available and parse_failures == 0
    return [
        _quality_gate(
            "qor.rcx.corner_coverage",
            "RCX corner coverage",
            _gate_state(available=coverage_available, passed=coverage_passed),
            [
                _quality_gate_metric(
                    "rcx_expected_corner_count", expected, ">", 0, expected_source
                ),
                _quality_gate_metric(
                    "rcx_spef_file_count", available, "==", expected, available_source
                ),
                _quality_gate_metric("rcx_missing_corner_count", missing, "==", 0, missing_source),
            ],
            _quality_gate_evidence(expected_source, available_source, missing_source),
        ),
        _quality_gate(
            "qor.rcx.spef_parse_health",
            "RCX SPEF integrity",
            _gate_state(available=parse_available, passed=parse_passed),
            [
                _quality_gate_metric(
                    "rcx_spef_parse_failure_count", parse_failures, "==", 0, parse_source
                )
            ],
            _quality_gate_evidence(parse_source),
        ),
    ]


def _sta_timing_closure_gate(
    gate_id: str,
    title: str,
    mode: str,
    signoff: dict,
    metric: MetricLookup,
    *,
    coverage_available: bool,
) -> dict:
    section = signoff.get(mode, {}) if isinstance(signoff, dict) else {}
    wns_id = f"sta_{mode}_wns"
    tns_id = f"sta_{mode}_tns"
    nvp_id = f"sta_{mode}_violation_count"
    wns, wns_source = metric(wns_id)
    tns, tns_source = metric(tns_id)
    nvp, nvp_source = metric(nvp_id)
    available = (
        coverage_available
        and all(value is not None for value in (wns, tns, nvp))
        and isinstance(section, dict)
    )
    passed = (
        available
        and isinstance(section, dict)
        and section.get("status") == "pass"
        and wns is not None
        and wns >= 0
        and tns is not None
        and tns >= 0
        and nvp == 0
    )
    return _quality_gate(
        gate_id,
        title,
        _gate_state(available=available, passed=passed),
        [
            _quality_gate_metric(wns_id, wns, ">=", 0, wns_source),
            _quality_gate_metric(tns_id, tns, ">=", 0, tns_source),
            _quality_gate_metric(nvp_id, nvp, "==", 0, nvp_source),
        ],
        _quality_gate_evidence(wns_source, tns_source, nvp_source),
    )


def _sta_gates(feature: dict, metric: MetricLookup) -> list[dict]:
    signoff = feature.get("sta", {}).get("signoff_metrics", {})
    coverage = signoff.get("coverage", {}) if isinstance(signoff, dict) else {}
    coverage_status = coverage.get("status") if isinstance(coverage, dict) else None
    coverage_available = coverage_status == "pass"

    drv_values = [metric(metric_id) for metric_id in STA_DRV_METRIC_IDS]
    drv_available = coverage_available and all(value is not None for value, _ in drv_values)
    drv_passed = drv_available and all(value == 0 for value, _ in drv_values)

    return [
        _sta_timing_closure_gate(
            "qor.sta.setup_closed",
            "STA setup closure",
            "setup",
            signoff,
            metric,
            coverage_available=coverage_available,
        ),
        _sta_timing_closure_gate(
            "qor.sta.hold_closed",
            "STA hold closure",
            "hold",
            signoff,
            metric,
            coverage_available=coverage_available,
        ),
        _quality_gate(
            "qor.sta.drv_clean",
            "STA max transition / capacitance / fanout",
            _gate_state(available=drv_available, passed=drv_passed),
            [
                _quality_gate_metric(metric_id, value, "==", 0, source)
                for metric_id, (value, source) in zip(STA_DRV_METRIC_IDS, drv_values, strict=True)
            ],
            _quality_gate_evidence(*(source for _, source in drv_values)),
        ),
    ]


def build_step_quality_gates(
    step: WorkspaceStep,
    records: list[dict],
    workspace: Workspace | None = None,
) -> list[dict]:
    """Build deterministic QoR signoff gates for *step* from extracted *records*."""
    records_by_id = {
        record.get("id"): record
        for record in records
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    }

    def metric(metric_id: str) -> tuple[int | float | None, dict | None]:
        record = records_by_id.get(metric_id, {})
        return qor_number(record.get("value")), record.get("source")

    if step.name == StepEnum.DRC.value:
        return _drc_gates(metric)
    if step.name == StepEnum.LVS.value:
        return _lvs_gates(metric)
    if step.name == StepEnum.ANTENNA_CHECK.value:
        return _antenna_gates(metric)
    if step.name == StepEnum.HARDEN.value:
        return _mpc_area_gates(workspace)

    feature = json_read(getattr(step.feature, "step", "") or "")
    feature = feature if isinstance(feature, dict) else {}

    if step.name == StepEnum.RCX.value:
        return _rcx_gates(feature, metric)
    if step.name == StepEnum.STA.value:
        return _sta_gates(feature, metric)

    return []
