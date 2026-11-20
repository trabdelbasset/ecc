"""Judge whether an antenna check actually analysed anything.

iMJ reports ``violation_count = 0`` and finishes successfully when the loaded
LEFs carry no antenna rules or no gate areas, so a clean count alone is not
evidence that the design was checked. Coverage is read from the counters in
``antenna_check.step.json``.
"""

from pathlib import Path

from chipcompiler.utility import json_read


def read_antenna_check(step_json: str | Path | None) -> dict | None:
    """Return the ``antenna_check`` block of the step JSON, or None when unreadable."""
    if not step_json:
        return None
    data = json_read(str(step_json))
    block = data.get("antenna_check") if isinstance(data, dict) else None
    return block if isinstance(block, dict) else None


def _count(block: dict, key: str) -> int | None:
    value = block.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return int(value)


_DIAGNOSTIC_KEYS = (
    "skipped_segments",
    "conductors_out_of_range",
    "partial_areas_dropped",
)


def antenna_diagnostics(block: dict | None) -> list[str]:
    """Return non-zero skipped/dropped geometry counters as strings."""
    if block is None:
        return []
    items = []
    for key in _DIAGNOSTIC_KEYS:
        val = _count(block, key)
        if val is not None and val > 0:
            items.append(f"{key}={val}")
    return items


def antenna_coverage(block: dict | None) -> tuple[bool, str]:
    """Return ``(verified, message)`` for an ``antenna_check`` block."""
    if block is None:
        return False, "Antenna check result is missing or unreadable; the design was not verified."
    nets = _count(block, "signal_net_count")
    pins = _count(block, "pins_with_gate_area")
    reasons = []
    if nets is None or nets <= 0:
        reasons.append("0 nets were analysed (no antenna rules in the loaded tech LEF?)")
    if pins is None or pins <= 0:
        reasons.append("0 gate pins have ANTENNAGATEAREA (missing in the cell LEFs?)")
    if reasons:
        return False, "Antenna check is not verified: " + "; ".join(reasons) + "."
    diags = antenna_diagnostics(block)
    base = f"Antenna check analysed {nets} nets and {pins} gate pins."
    if diags:
        return True, f"{base} Diagnostics: {', '.join(diags)}."
    return True, base
