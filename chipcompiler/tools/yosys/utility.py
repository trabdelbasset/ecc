#!/usr/bin/env python
import os
import re
import shutil
import subprocess
from pathlib import Path

MIN_YOSYS_VERSION: tuple[int, ...] = (0, 67)
MIN_YOSYS_VERSION_STR = "0.67"
_YOSYS_VERSION_RE = re.compile(r"^(?:Yosys\s+)?(\d+(?:\.\d+)+)(?:\+\d+)?(?=$|\s)")


def _sanitize_loader_env(env: dict[str, str]) -> dict[str, str]:
    """Remove loader-related env vars that can break bundled yosys launcher."""
    env.pop("LD_LIBRARY_PATH", None)
    env.pop("LD_PRELOAD", None)
    return env


def _build_oss_cad_env(oss_path: Path, base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Build subprocess environment variables for OSS CAD Suite."""
    # TODO: Useless in nix build, consider remove this?
    env = dict(base_env) if base_env is not None else os.environ.copy()

    bin_dir = str(oss_path / "bin")
    current_path = env.get("PATH", "")
    if bin_dir not in current_path.split(os.pathsep):
        env["PATH"] = f"{bin_dir}{os.pathsep}{current_path}".rstrip(os.pathsep)

    share_dir = oss_path / "share" / "yosys"
    if (share_dir / "plugins").exists():
        env.setdefault("YOSYS_PLUGINPATH", str(share_dir / "plugins"))
    if (share_dir / "techlibs").exists():
        env.setdefault("YOSYS_DATDIR", str(share_dir))

    return env


def _resolve_oss_yosys_paths() -> tuple[str, Path | None, Path | None]:
    """
    Resolve OSS CAD root and expected yosys binary path from environment.
    """
    oss_cad_dir = os.environ.get("CHIPCOMPILER_OSS_CAD_DIR", "").strip()
    if not oss_cad_dir:
        return "", None, None

    oss_path = Path(oss_cad_dir)
    yosys_bin = oss_path / "bin" / ("yosys.exe" if os.name == "nt" else "yosys")
    return oss_cad_dir, oss_path, yosys_bin


def _resolve_yosys_command() -> tuple[list[str], Path | None]:
    """
    Resolve yosys executable from bundled runtime first, then system PATH.

    Returns:
        (command, oss_path):
            - command: list containing executable command or empty list if unavailable
            - oss_path: OSS CAD root path if bundled yosys is selected, else None
    """
    _, oss_path, yosys_bin = _resolve_oss_yosys_paths()
    if oss_path is not None and yosys_bin is not None and yosys_bin.exists():
        return [str(yosys_bin)], oss_path

    if shutil.which("yosys"):
        return ["yosys"], None

    return [], None


def get_yosys_not_found_error() -> str:
    """
    Build a clear error message when yosys cannot be resolved.
    """
    oss_cad_dir, _, yosys_bin = _resolve_oss_yosys_paths()
    if oss_cad_dir and yosys_bin is not None:
        return (
            "Yosys executable not found. "
            f"Checked CHIPCOMPILER_OSS_CAD_DIR='{oss_cad_dir}' "
            f"(expected binary at '{yosys_bin}') and system PATH. "
            "Please install yosys or fix CHIPCOMPILER_OSS_CAD_DIR."
        )

    return (
        "Yosys executable not found in system PATH, and CHIPCOMPILER_OSS_CAD_DIR "
        "is not set. Please install yosys or set CHIPCOMPILER_OSS_CAD_DIR "
        "to the OSS CAD Suite root directory."
    )


def get_yosys_command() -> list[str]:
    """
    Get the yosys command to use.

    Checks bundled runtime first, then PATH.
    This function is side-effect free and never mutates os.environ.
    """
    command, _ = _resolve_yosys_command()
    return command


def get_yosys_runtime() -> tuple[list[str], dict[str, str]]:
    """
    Get yosys command and subprocess environment.

    Environment variables are only prepared for the subprocess and never
    written to global os.environ.
    """
    command, oss_path = _resolve_yosys_command()
    env = _sanitize_loader_env(os.environ.copy())
    if oss_path is not None:
        env = _build_oss_cad_env(oss_path=oss_path, base_env=env)
    return command, env


def check_slang_support(
    yosys_cmd: list[str], cwd_dir: str, yosys_env: dict[str, str], log_file, timeout: int = 60
) -> bool:
    """
    Run a lightweight slang frontend availability check.

    Since v0.67 yosys enables the slang frontend by default
    (https://github.com/YosysHQ/yosys/releases/tag/v0.67); older builds
    ship it as a plugin loaded via `plugin -i slang`. Accept either form.
    """
    # `help` exits 0 even for unknown commands, so inspect the output text.
    builtin_check = subprocess.run(
        yosys_cmd + ["-Q", "-T", "-p", "help read_slang"],
        cwd=cwd_dir,
        env=yosys_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if builtin_check.returncode == 0 and b"No such command" not in builtin_check.stdout:
        return True

    plugin_check = subprocess.run(
        yosys_cmd + ["-Q", "-T", "-p", "plugin -i slang"],
        cwd=cwd_dir,
        env=yosys_env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if plugin_check.returncode == 0:
        return True

    error_msg = (
        "Error: yosys slang frontend check failed. "
        "Neither builtin read_slang nor a loadable slang plugin was found. "
        "Please use a yosys build with slang support."
    )
    log_file.write(error_msg + "\n")
    print(error_msg)
    return False


def extract_yosys_version_token(output: str) -> str:
    """Extract the version token from ``yosys -V`` output."""
    stripped = output.strip()
    if not stripped:
        return ""
    parts = stripped.split()
    if parts[0] == "Yosys" and len(parts) > 1:
        return parts[1]
    return stripped


def parse_yosys_version(output: str) -> tuple[int, ...] | None:
    """Parse major/minor version components from ``yosys -V`` or its version token."""
    match = _YOSYS_VERSION_RE.search(output.strip())
    if match is None:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def get_yosys_version_string(
    yosys_cmd: list[str], yosys_env: dict[str, str], timeout: int = 5
) -> str | None:
    """Query ``yosys -V`` and return the extracted version token, or None on failure."""
    try:
        result = subprocess.run(
            yosys_cmd + ["-V"],
            env=yosys_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    output = result.stdout.decode("utf-8", errors="replace").strip()
    if not output:
        return None
    return extract_yosys_version_token(output)


def check_yosys_version(
    yosys_cmd: list[str],
    yosys_env: dict[str, str],
    *,
    min_version: tuple[int, ...] = MIN_YOSYS_VERSION,
    timeout: int = 5,
) -> tuple[bool, str | None, str]:
    """Verify Yosys meets ``min_version``; return ``(ok, version_str, error_message)``."""
    min_label = ".".join(str(part) for part in min_version)
    version_str = get_yosys_version_string(yosys_cmd, yosys_env, timeout=timeout)
    if version_str is None:
        return (
            False,
            None,
            f"Could not determine Yosys version from '{' '.join(yosys_cmd)} -V'. "
            f"ECC requires Yosys >= {min_label} (OSS CAD Suite).",
        )
    parsed = parse_yosys_version(version_str)
    if parsed is None:
        return (
            False,
            version_str,
            f"Unrecognized Yosys version {version_str!r}. "
            f"ECC requires Yosys >= {min_label} (OSS CAD Suite).",
        )
    if parsed < min_version:
        return (
            False,
            version_str,
            f"Yosys {version_str} is older than required >= {min_label}. "
            f"Install OSS CAD Suite / Yosys >= {min_label} (or set CHIPCOMPILER_OSS_CAD_DIR).",
        )
    return True, version_str, ""


def is_eda_exist() -> bool:
    """
    Check if yosys is available via bundled runtime or PATH.
    """
    if get_yosys_command():
        return True

    raise RuntimeError(get_yosys_not_found_error())
