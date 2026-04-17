#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from dataclasses import dataclass, field
import json
import logging
import os

logger = logging.getLogger(__name__)

ECC_PDK_CONFIG_FILENAME = "ecc_pdk.json"

@dataclass
class PDK:
    """
    Dataclass for PDK information
    """
    name : str = "" # pdk name
    version : str = "" # pdk version
    root : str = "" # resolved pdk root path
    tech : str = "" # pdk tech lef file
    lefs : list = field(default_factory=list) # pdk lef files
    libs : list = field(default_factory=list) # pdk liberty files
    sdc : str = "" # pdk sdc file
    spef : str = "" # pdk spef file
    site_core : str = "" # core site
    site_io : str = "" # io site
    site_corner : str = "" # corner site
    tap_cell : str = "" # tap cell
    end_cap : str = "" # end cap
    buffers : list = field(default_factory=list) # buffers
    fillers : list = field(default_factory=list) # fillers
    tie_high_cell : str = ""
    tie_high_port : str = ""
    tie_low_cell : str = ""
    tie_low_port : str = ""
    dont_use : list = field(default_factory=list) # don't use cell list

    def validate(self) -> None:
        """Check that critical PDK paths exist. Raises ValueError if not."""
        errors = []
        if self.root and not os.path.isdir(self.root):
            errors.append(f"PDK root directory not found: {self.root}")
        if not self.tech:
            errors.append("PDK tech LEF is missing")
        if not self.lefs:
            errors.append("PDK has no LEF files")
        if not self.libs:
            errors.append("PDK has no liberty files")
        if errors:
            msg = "PDK validation failed:\n  " + "\n  ".join(errors)
            logger.error(msg)
            raise ValueError(msg)

def _resolve_pdk_root(pdk_root: str, env_vars: list) -> str:
    candidate = (pdk_root or "").strip()
    if not candidate:
        for var in env_vars:
            candidate = os.environ.get(var, "").strip()
            if candidate:
                break
    if not candidate:
        return ""
    return os.path.abspath(os.path.expanduser(candidate))

def _find_pdk_config(pdk_root: str) -> str:
    """Return path to ecc_pdk.json inside pdk_root, or empty string."""
    if not pdk_root:
        return ""
    config_path = os.path.join(pdk_root, ECC_PDK_CONFIG_FILENAME)
    if os.path.isfile(config_path):
        return config_path
    return ""

def _resolve_env_vars_for_pdk(pdk_name: str) -> list:
    """Return the standard env var names for a given PDK name."""
    upper = pdk_name.upper()
    return [
        f"CHIPCOMPILER_{upper}_PDK_ROOT",
        f"{upper}_PDK_ROOT",
    ]

def load_pdk_from_json(pdk_root: str) -> PDK:
    """
    Load a PDK configuration from ecc_pdk.json in the given pdk_root.
    File paths in the JSON are relative to pdk_root and resolved to absolute.
    Raises ValueError if the config file is missing or malformed.
    """
    config_path = _find_pdk_config(pdk_root)
    if not config_path:
        raise ValueError(
            f"PDK config file '{ECC_PDK_CONFIG_FILENAME}' not found in: {pdk_root}"
        )

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(
            f"Failed to read PDK config '{config_path}': {e}"
        )

    files = config.get("files", {})
    cells = config.get("cells", {})

    tech_rel = files.get("tech_lef", "")
    tech_path = os.path.join(pdk_root, tech_rel) if tech_rel else ""

    lef_paths = [
        os.path.join(pdk_root, p) for p in files.get("lefs", [])
    ]
    lib_paths = [
        os.path.join(pdk_root, p) for p in files.get("libs", [])
    ]

    pdk = PDK(
        name=config.get("name", ""),
        version=config.get("version", ""),
        root=pdk_root,
        tech=tech_path if tech_path and os.path.isfile(tech_path) else "",
        lefs=[path for path in lef_paths if os.path.isfile(path)],
        libs=[path for path in lib_paths if os.path.isfile(path)],
        site_core=cells.get("site_core", ""),
        site_io=cells.get("site_io", ""),
        site_corner=cells.get("site_corner", ""),
        tap_cell=cells.get("tap_cell", ""),
        end_cap=cells.get("end_cap", ""),
        buffers=cells.get("buffers", []),
        fillers=cells.get("fillers", []),
        tie_high_cell=cells.get("tie_high_cell", ""),
        tie_high_port=cells.get("tie_high_port", ""),
        tie_low_cell=cells.get("tie_low_cell", ""),
        tie_low_port=cells.get("tie_low_port", ""),
        dont_use=cells.get("dont_use", []),
    )

    return pdk

def get_pdk(pdk_name : str, pdk_root: str = "") -> PDK:
    """
    Return the PDK instance based on the given pdk name.

    - "ics55": uses the hardcoded ICS55 configuration.
    - Any other name: loads from ecc_pdk.json in the resolved pdk_root.
    """
    pdk_name_normalized = (pdk_name or "").strip().lower()
    if pdk_name_normalized == "ics55":
        pdk = PDK_ICS55(pdk_root=pdk_root)
    else:
        env_vars = _resolve_env_vars_for_pdk(pdk_name_normalized)
        resolved_root = _resolve_pdk_root(pdk_root, env_vars)
        pdk = load_pdk_from_json(resolved_root)
    pdk.validate()
    return pdk

def PDK_ICS55(pdk_root: str = "") -> PDK:
    current_dir = os.path.split(os.path.abspath(__file__))[0]
    root = current_dir.rsplit('/', 2)[0]
    default_pdk_root = "{}/chipcompiler/thirdparty/icsprout55-pdk".format(root)
    resolved_root = _resolve_pdk_root(
        pdk_root,
        ["CHIPCOMPILER_ICS55_PDK_ROOT", "ICS55_PDK_ROOT"]
    ) or os.path.abspath(default_pdk_root)

    stdcell_dir = "{}/IP/STD_cell/ics55_LLSC_H7C_V1p10C100".format(resolved_root)

    tech_path = "{}/prtech/techLEF/N551P6M.lef".format(resolved_root)
    lef_paths = [
        "{}/ics55_LLSC_H7CR/lef/ics55_LLSC_H7CR_ecos.lef".format(stdcell_dir),
        "{}/ics55_LLSC_H7CL/lef/ics55_LLSC_H7CL_ecos.lef".format(stdcell_dir)
    ]
    lib_paths = [
        "{}/ics55_LLSC_H7CR/liberty/ics55_LLSC_H7CR_ss_rcworst_1p08_125_nldm.lib".format(stdcell_dir),
        "{}/ics55_LLSC_H7CL/liberty/ics55_LLSC_H7CL_ss_rcworst_1p08_125_nldm.lib".format(stdcell_dir)
    ]

    pdk = PDK(
        name="ics55",
        version="V1p10C100",
        root=resolved_root,
        tech=tech_path if os.path.isfile(tech_path) else "",
        lefs=[path for path in lef_paths if os.path.isfile(path)],
        libs=[path for path in lib_paths if os.path.isfile(path)],
        site_core = "core7",
        site_io = "core7",
        site_corner = "core7",
        tap_cell = "FILLTAPH7R",
        end_cap = "FILLTAPH7R",
        buffers = [
            "BUFX8H7L",
            "BUFX12H7L",
            "BUFX16H7L",
            "BUFX20H7L"
        ],
        fillers = [
            "FILLER64H7R",
            "FILLER32H7R",
            "FILLER16H7R",
            "FILLER8H7R",
            "FILLER4H7R",
            "FILLER2H7R",
            "FILLER1H7R" 
        ],
        tie_high_cell = "TIEHIH7R",
        tie_high_port = "Z",
        tie_low_cell = "TIELOH7R",
        tie_low_port = "Z",
        dont_use=[
            "DFFSRQX*",
            "DFFSRX*",
            "*AO222*",
            "*2BB2*",
            "*AOI222*",
            "*AOI33*",
            "*OA222*",
            "*OAI222*",
            "*OAI33*",
            "*NOR4*",
            "ICG*"
        ]
    )

    return pdk