import pytest

from chipcompiler.analysis.qor.feasibility import evaluate_feasibility
from test.analysis.qor.helpers import gcd_metrics, make_inputs, make_metric

SUCCESS = "Success"


def _antenna_gate(violations=None, nets=None, state=SUCCESS, *, in_flow=True):
    metrics = gcd_metrics()
    if violations is not None:
        metrics["antenna_violation_count"] = make_metric(
            "antenna_violation_count", violations, step="antenna_check"
        )
    if nets is not None:
        metrics["antenna_signal_net_count"] = make_metric(
            "antenna_signal_net_count", nets, step="antenna_check"
        )
    inputs = make_inputs(metrics, tclk_ns=20.0)
    if in_flow:
        inputs.flow_states["antenna_check"] = state
    feasibility = evaluate_feasibility(inputs)
    gate = next((g for g in feasibility.gates if g.id == "GATE_ANTENNA"), None)
    return feasibility, gate


def test_gate_is_skipped_for_flows_without_antenna_step():
    feasibility, gate = _antenna_gate(in_flow=False)
    assert gate is None
    assert feasibility.status == "PASS"


def test_analysed_clean_antenna_check_passes():
    feasibility, gate = _antenna_gate(violations=0, nets=4213)
    assert gate.state == "passed"
    assert feasibility.status == "PASS"


@pytest.mark.parametrize("violations", [1, 37])
def test_antenna_violations_are_a_physical_fail(violations):
    feasibility, gate = _antenna_gate(violations=violations, nets=4213)
    assert gate.state == "failed"
    assert gate.blocks_tapeout is True
    assert feasibility.status == "PHYSICAL_FAIL"


def test_vacuous_antenna_check_is_not_verified_not_pass():
    feasibility, gate = _antenna_gate(violations=0, nets=0)
    assert gate.state == "unavailable"
    assert gate.availability == "not_verified"
    assert feasibility.status == "NOT_VERIFIED"


def test_failed_antenna_step_is_not_verified():
    feasibility, gate = _antenna_gate(violations=0, nets=10, state="Incomplete")
    assert gate.availability == "not_verified"
    assert feasibility.status == "NOT_VERIFIED"


def test_missing_violation_metric_is_corrupt_evidence():
    feasibility, gate = _antenna_gate(nets=10)
    assert gate.availability == "corrupt"
    assert feasibility.status == "UNKNOWN"
