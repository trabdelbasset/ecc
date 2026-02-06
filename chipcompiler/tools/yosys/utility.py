#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import os
import shutil
from pathlib import Path


def _setup_oss_cad_env(oss_path: Path) -> None:
    """Configure environment variables for OSS CAD Suite."""
    bin_dir = str(oss_path / "bin")
    current_path = os.environ.get("PATH", "")
    if bin_dir not in current_path.split(os.pathsep):
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{current_path}".rstrip(os.pathsep)

    share_dir = oss_path / "share" / "yosys"
    if (share_dir / "plugins").exists():
        os.environ.setdefault("YOSYS_PLUGINPATH", str(share_dir / "plugins"))
    if (share_dir / "techlibs").exists():
        os.environ.setdefault("YOSYS_DATDIR", str(share_dir))


def get_yosys_command() -> list[str]:
    """
    Get the yosys command to use.

    Checks if 'yosys' is available in PATH (from nix develop, OSS CAD Suite, or system install).
    """
    if oss_cad_dir := os.environ.get("CHIPCOMPILER_OSS_CAD_DIR"):
        oss_path = Path(oss_cad_dir)
        yosys_bin = oss_path / "bin" / ("yosys.exe" if os.name == "nt" else "yosys")
        if yosys_bin.exists():
            _setup_oss_cad_env(oss_path)
            return [str(yosys_bin)]

    return ["yosys"] if shutil.which("yosys") else []


def is_eda_exist() -> bool:
    """
    Check if yosys is available in PATH.
    """
    return bool(get_yosys_command())
