#!/usr/bin/env python

import json
from pathlib import Path

import pytest

from chipcompiler.data.pdk import get_pdk, ECC_PDK_CONFIG_FILENAME


def _create_minimal_ics55_pdk(root: Path) -> Path:
    """Create the minimal ICS55 directory tree required by get_pdk()."""
    tech_path = root / "prtech" / "techLEF" / "N551P6M.lef"
    tech_path.parent.mkdir(parents=True, exist_ok=True)
    tech_path.write_text("VERSION 5.8 ;\n")

    stdcell_root = root / "IP" / "STD_cell" / "ics55_LLSC_H7C_V1p10C100"
    for flavor in ("ics55_LLSC_H7CR", "ics55_LLSC_H7CL"):
        lef_path = stdcell_root / flavor / "lef" / f"{flavor}_ecos.lef"
        lef_path.parent.mkdir(parents=True, exist_ok=True)
        lef_path.write_text("VERSION 5.8 ;\n")

        lib_path = stdcell_root / flavor / "liberty" / f"{flavor}_ss_rcworst_1p08_125_nldm.lib"
        lib_path.parent.mkdir(parents=True, exist_ok=True)
        lib_path.write_text("library(test) { }\n")

    return root


def test_get_pdk_prefers_explicit_root_over_env(tmp_path, monkeypatch):
    explicit_root = _create_minimal_ics55_pdk(tmp_path / "explicit")
    env_root = _create_minimal_ics55_pdk(tmp_path / "env")
    monkeypatch.setenv("CHIPCOMPILER_ICS55_PDK_ROOT", str(env_root))

    pdk = get_pdk("ics55", pdk_root=str(explicit_root))

    expected_root = str(explicit_root.resolve())
    assert pdk.root == expected_root
    assert pdk.tech.startswith(expected_root)
    assert all(path.startswith(expected_root) for path in pdk.lefs + pdk.libs)


def test_get_pdk_uses_namespaced_env(tmp_path, monkeypatch):
    env_root = _create_minimal_ics55_pdk(tmp_path / "env")
    monkeypatch.setenv("CHIPCOMPILER_ICS55_PDK_ROOT", str(env_root))
    monkeypatch.delenv("ICS55_PDK_ROOT", raising=False)

    pdk = get_pdk("ics55")

    assert pdk.root == str(env_root.resolve())


def test_get_pdk_uses_legacy_env_when_namespaced_missing(tmp_path, monkeypatch):
    legacy_root = _create_minimal_ics55_pdk(tmp_path / "legacy")
    monkeypatch.delenv("CHIPCOMPILER_ICS55_PDK_ROOT", raising=False)
    monkeypatch.setenv("ICS55_PDK_ROOT", str(legacy_root))

    pdk = get_pdk("ics55")

    assert pdk.root == str(legacy_root.resolve())


def test_get_pdk_raises_on_missing_pdk_files(tmp_path):
    invalid_root = tmp_path / "broken_ics55"
    invalid_root.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="PDK validation failed"):
        get_pdk("ics55", pdk_root=str(invalid_root))


#SG13G2 helpers and tests

def _sg13g2_pdk_config() -> dict:
    """Return a minimal ecc_pdk.json config dict for SG13G2."""
    return {
        "name": "sg13g2",
        "version": "1.0",
        "env_vars": [
            "CHIPCOMPILER_SG13G2_PDK_ROOT",
            "SG13G2_PDK_ROOT"
        ],
        "files": {
            "tech_lef": "libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef",
            "lefs": ["libs.ref/sg13g2_stdcell/lef/sg13g2_stdcell.lef"],
            "libs": ["libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib"]
        },
        "cells": {
            "site_core": "CoreSite",
            "site_io": "",
            "site_corner": "",
            "tap_cell": "",
            "end_cap": "",
            "buffers": [
                "sg13g2_buf_1", "sg13g2_buf_2", "sg13g2_buf_4",
                "sg13g2_buf_8", "sg13g2_buf_16"
            ],
            "fillers": [
                "sg13g2_fill_1", "sg13g2_fill_2",
                "sg13g2_decap_4", "sg13g2_decap_8"
            ],
            "tie_high_cell": "sg13g2_tiehi",
            "tie_high_port": "L_HI",
            "tie_low_cell": "sg13g2_tielo",
            "tie_low_port": "L_LO",
            "dont_use": [
                "sg13g2_lgcp_1", "sg13g2_sighold",
                "sg13g2_slgcp_1", "sg13g2_dfrbp_2"
            ]
        },
        "parameters": {}
    }


def _create_minimal_sg13g2_pdk(root: Path) -> Path:
    """Create the minimal SG13G2 directory tree and ecc_pdk.json."""
    tech_path = root / "libs.ref" / "sg13g2_stdcell" / "lef" / "sg13g2_tech.lef"
    tech_path.parent.mkdir(parents=True, exist_ok=True)
    tech_path.write_text("VERSION 5.8 ;\n")

    lef_path = root / "libs.ref" / "sg13g2_stdcell" / "lef" / "sg13g2_stdcell.lef"
    lef_path.write_text("VERSION 5.8 ;\n")

    lib_path = root / "libs.ref" / "sg13g2_stdcell" / "lib" / "sg13g2_stdcell_typ_1p20V_25C.lib"
    lib_path.parent.mkdir(parents=True, exist_ok=True)
    lib_path.write_text("library(test) { }\n")

    config_path = root / ECC_PDK_CONFIG_FILENAME
    config_path.write_text(json.dumps(_sg13g2_pdk_config(), indent=4))

    return root


def test_get_pdk_sg13g2_prefers_explicit_root_over_env(tmp_path, monkeypatch):
    explicit_root = _create_minimal_sg13g2_pdk(tmp_path / "explicit")
    env_root = _create_minimal_sg13g2_pdk(tmp_path / "env")
    monkeypatch.setenv("CHIPCOMPILER_SG13G2_PDK_ROOT", str(env_root))

    pdk = get_pdk("sg13g2", pdk_root=str(explicit_root))

    expected_root = str(explicit_root.resolve())
    assert pdk.root == expected_root
    assert pdk.tech.startswith(expected_root)
    assert all(path.startswith(expected_root) for path in pdk.lefs + pdk.libs)


def test_get_pdk_sg13g2_uses_namespaced_env(tmp_path, monkeypatch):
    env_root = _create_minimal_sg13g2_pdk(tmp_path / "env")
    monkeypatch.setenv("CHIPCOMPILER_SG13G2_PDK_ROOT", str(env_root))
    monkeypatch.delenv("SG13G2_PDK_ROOT", raising=False)

    pdk = get_pdk("sg13g2")

    assert pdk.root == str(env_root.resolve())


def test_get_pdk_sg13g2_uses_legacy_env_when_namespaced_missing(tmp_path, monkeypatch):
    legacy_root = _create_minimal_sg13g2_pdk(tmp_path / "legacy")
    monkeypatch.delenv("CHIPCOMPILER_SG13G2_PDK_ROOT", raising=False)
    monkeypatch.setenv("SG13G2_PDK_ROOT", str(legacy_root))

    pdk = get_pdk("sg13g2")

    assert pdk.root == str(legacy_root.resolve())


def test_get_pdk_sg13g2_raises_on_missing_pdk_files(tmp_path, monkeypatch):
    invalid_root = tmp_path / "broken_sg13g2"
    invalid_root.mkdir(parents=True, exist_ok=True)
    # Write config but no actual files
    config = _sg13g2_pdk_config()
    (invalid_root / ECC_PDK_CONFIG_FILENAME).write_text(json.dumps(config))
    monkeypatch.setenv("CHIPCOMPILER_SG13G2_PDK_ROOT", str(invalid_root))

    with pytest.raises(ValueError, match="PDK validation failed"):
        get_pdk("sg13g2")


def test_get_pdk_sg13g2_cell_config(tmp_path, monkeypatch):
    pdk_root = _create_minimal_sg13g2_pdk(tmp_path / "sg13g2")
    monkeypatch.setenv("CHIPCOMPILER_SG13G2_PDK_ROOT", str(pdk_root))

    pdk = get_pdk("sg13g2")

    assert pdk.name == "sg13g2"
    assert pdk.site_core == "CoreSite"
    assert pdk.tie_high_cell == "sg13g2_tiehi"
    assert pdk.tie_high_port == "L_HI"
    assert pdk.tie_low_cell == "sg13g2_tielo"
    assert pdk.tie_low_port == "L_LO"
    assert "sg13g2_buf_1" in pdk.buffers
    assert "sg13g2_fill_1" in pdk.fillers
    assert "sg13g2_lgcp_1" in pdk.dont_use


def test_get_pdk_sg13g2_case_insensitive(tmp_path, monkeypatch):
    pdk_root = _create_minimal_sg13g2_pdk(tmp_path / "sg13g2")
    monkeypatch.setenv("CHIPCOMPILER_SG13G2_PDK_ROOT", str(pdk_root))

    pdk = get_pdk("SG13G2")

    assert pdk.name == "sg13g2"


def test_get_pdk_json_missing_config_raises(tmp_path, monkeypatch):
    """Error when pdk_root exists but has no ecc_pdk.json."""
    empty_root = tmp_path / "no_config"
    empty_root.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="ecc_pdk.json"):
        get_pdk("some_pdk", pdk_root=str(empty_root))


def test_get_pdk_json_invalid_config_raises(tmp_path, monkeypatch):
    """Error when ecc_pdk.json exists but contains invalid JSON."""
    bad_root = tmp_path / "bad_json"
    bad_root.mkdir(parents=True, exist_ok=True)
    (bad_root / ECC_PDK_CONFIG_FILENAME).write_text("{invalid json!!!")

    with pytest.raises(ValueError, match="Failed to read PDK config"):
        get_pdk("bad_pdk", pdk_root=str(bad_root))
