import json
from pathlib import Path

from chipcompiler.data import get_design_parameters, get_parameters
from chipcompiler.data.pdk import ECC_PDK_CONFIG_FILENAME


def test_get_design_parameters_ics55_gcd_overrides_fields():
    parameters = get_design_parameters("ics55", "gcd")

    assert parameters.data["Design"] == "gcd"
    assert parameters.data["Top module"] == "gcd"
    assert parameters.data["Clock"] == "clk"
    assert parameters.data["Frequency max [MHz]"] == 100


def test_get_design_parameters_ics55_empty_design_returns_base_template():
    parameters = get_design_parameters("ics55", "")

    assert parameters.data["Design"] == ""
    assert parameters.data["Top module"] == ""
    assert parameters.data["Clock"] == ""
    assert parameters.data["Frequency max [MHz]"] == 100


def test_get_design_parameters_ics55_unknown_design_returns_base_template():
    parameters = get_design_parameters("ics55", "unknown_design")

    assert parameters.data["Design"] == ""
    assert parameters.data["Top module"] == ""
    assert parameters.data["Clock"] == ""
    assert parameters.data["Frequency max [MHz]"] == 100


def test_get_parameters_returns_independent_copies():
    first = get_parameters("ics55")
    second = get_parameters("ics55")

    first.data["Design"] = "mutated"
    first.data["Floorplan"]["Tracks"][0]["x step"] = 999

    assert second.data["Design"] == ""
    assert second.data["Floorplan"]["Tracks"][0]["x step"] == 200


def test_ics55_template_has_dreamplace_padding_defaults():
    parameters = get_parameters("ics55")

    assert parameters.data["Cell padding x"] == 600
    assert parameters.data["Routability opt flag"] == 1


#SG13G2 parameter tests

def _sg13g2_parameters_template() -> dict:
    """Return the SG13G2 parameters template for use in ecc_pdk.json."""
    return {
        "PDK": "sg13g2",
        "Design": "",
        "Top module": "",
        "Die": {"Size": [], "Area": 0},
        "Core": {
            "Size": [], "Area": 0, "Bounding box": "",
            "Utilitization": 0.65, "Margin": [17.5, 17.5], "Aspect ratio": 1
        },
        "Max fanout": 20,
        "Target density": 0.65,
        "Target overflow": 0.1,
        "Global right padding": 0,
        "Cell padding x": 0,
        "Routability opt flag": 1,
        "Clock": "",
        "Frequency max [MHz]": 100,
        "Bottom layer": "Metal2",
        "Top layer": "Metal5",
        "Floorplan": {
            "Tap distance": 0,
            "Auto place pin": {
                "layer": "Metal3", "width": 300, "height": 600, "sides": []
            },
            "Tracks": [
                {"layer": "Metal1", "x start": 0, "x step": 420, "y start": 0, "y step": 420},
                {"layer": "Metal2", "x start": 0, "x step": 480, "y start": 0, "y step": 480},
                {"layer": "Metal3", "x start": 0, "x step": 420, "y start": 0, "y step": 420},
                {"layer": "Metal4", "x start": 0, "x step": 480, "y start": 0, "y step": 480},
                {"layer": "Metal5", "x start": 0, "x step": 420, "y start": 0, "y step": 420},
            ]
        },
        "PDN": {
            "IO": [
                {"net name": "VDD", "direction": "INOUT", "is power": True},
                {"net name": "VSS", "direction": "INOUT", "is power": False}
            ],
            "Global connect": [
                {"net name": "VDD", "instance pin name": "VDD", "is power": True},
                {"net name": "VSS", "instance pin name": "VSS", "is power": False}
            ],
            "Grid": {
                "layer": "Metal1", "power net": "VDD",
                "power ground": "VSS", "width": 0.44, "offset": 0
            },
            "Stripe": [
                {"layer": "Metal4", "power net": "VDD", "ground net": "VSS", "width": 1.6, "pitch": 20, "offset": 1},
                {"layer": "Metal5", "power net": "VDD", "ground net": "VSS", "width": 1.6, "pitch": 20, "offset": 1}
            ],
            "Connect layers": [
                {"layers": ["Metal1", "Metal5"]},
                {"layers": ["Metal4", "Metal5"]}
            ]
        }
    }


def _create_sg13g2_pdk_config(root: Path) -> Path:
    """Write an ecc_pdk.json with parameters into root. Returns root."""
    root.mkdir(parents=True, exist_ok=True)
    config = {
        "name": "sg13g2",
        "version": "1.0",
        "env_vars": ["CHIPCOMPILER_SG13G2_PDK_ROOT", "SG13G2_PDK_ROOT"],
        "files": {"tech_lef": "", "lefs": [], "libs": []},
        "cells": {},
        "parameters": _sg13g2_parameters_template()
    }
    (root / ECC_PDK_CONFIG_FILENAME).write_text(json.dumps(config, indent=4))
    return root


def test_get_parameters_sg13g2_returns_template(tmp_path, monkeypatch):
    _create_sg13g2_pdk_config(tmp_path / "sg13g2")
    monkeypatch.setenv("CHIPCOMPILER_SG13G2_PDK_ROOT", str(tmp_path / "sg13g2"))

    parameters = get_parameters("sg13g2")

    assert parameters.data["PDK"] == "sg13g2"
    assert parameters.data["Design"] == ""
    assert parameters.data["Top module"] == ""
    assert parameters.data["Clock"] == ""
    assert parameters.data["Frequency max [MHz]"] == 100


def test_get_parameters_sg13g2_returns_independent_copies(tmp_path, monkeypatch):
    _create_sg13g2_pdk_config(tmp_path / "sg13g2")
    monkeypatch.setenv("CHIPCOMPILER_SG13G2_PDK_ROOT", str(tmp_path / "sg13g2"))

    first = get_parameters("sg13g2")
    second = get_parameters("sg13g2")

    first.data["Design"] = "mutated"
    first.data["Floorplan"]["Tracks"][0]["x step"] = 999

    assert second.data["Design"] == ""
    assert second.data["Floorplan"]["Tracks"][0]["x step"] == 420


def test_sg13g2_template_has_correct_layer_names(tmp_path, monkeypatch):
    _create_sg13g2_pdk_config(tmp_path / "sg13g2")
    monkeypatch.setenv("CHIPCOMPILER_SG13G2_PDK_ROOT", str(tmp_path / "sg13g2"))

    parameters = get_parameters("sg13g2")

    assert parameters.data["Bottom layer"] == "Metal2"
    assert parameters.data["Top layer"] == "Metal5"


def test_sg13g2_template_has_correct_core_defaults(tmp_path, monkeypatch):
    _create_sg13g2_pdk_config(tmp_path / "sg13g2")
    monkeypatch.setenv("CHIPCOMPILER_SG13G2_PDK_ROOT", str(tmp_path / "sg13g2"))

    parameters = get_parameters("sg13g2")

    assert parameters.data["Core"]["Utilitization"] == 0.65
    assert parameters.data["Core"]["Margin"] == [17.5, 17.5]
    assert parameters.data["Target density"] == 0.65


def test_sg13g2_template_has_dreamplace_padding_defaults(tmp_path, monkeypatch):
    _create_sg13g2_pdk_config(tmp_path / "sg13g2")
    monkeypatch.setenv("CHIPCOMPILER_SG13G2_PDK_ROOT", str(tmp_path / "sg13g2"))

    parameters = get_parameters("sg13g2")

    assert parameters.data["Cell padding x"] == 0
    assert parameters.data["Routability opt flag"] == 1


def test_sg13g2_template_pdn_has_two_power_nets(tmp_path, monkeypatch):
    _create_sg13g2_pdk_config(tmp_path / "sg13g2")
    monkeypatch.setenv("CHIPCOMPILER_SG13G2_PDK_ROOT", str(tmp_path / "sg13g2"))

    parameters = get_parameters("sg13g2")

    io_nets = parameters.data["PDN"]["IO"]
    assert len(io_nets) == 2
    net_names = [n["net name"] for n in io_nets]
    assert "VDD" in net_names
    assert "VSS" in net_names


def test_get_design_parameters_sg13g2_returns_base_template(tmp_path, monkeypatch):
    """SG13G2 has no design-specific overrides, so any design name returns the base template."""
    _create_sg13g2_pdk_config(tmp_path / "sg13g2")
    monkeypatch.setenv("CHIPCOMPILER_SG13G2_PDK_ROOT", str(tmp_path / "sg13g2"))

    parameters = get_design_parameters("sg13g2", "gcd")

    assert parameters.data["PDK"] == "sg13g2"
    assert parameters.data["Design"] == ""
    assert parameters.data["Top module"] == ""
