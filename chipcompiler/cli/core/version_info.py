from importlib import import_module, metadata

UNKNOWN_VERSION = "unknown"
RUNTIME_LABEL = "ECC CLI"
VERSION_SCHEMA = 2
CLI_CONTRACT = 1


def distribution_version(distribution: str, fallback: str | None = None) -> str:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return fallback or UNKNOWN_VERSION


def build_identity() -> tuple[str | None, str | None]:
    """Return the (commit, yyyymmdd) pair CI stamps into packaged bundles.

    Source and editable installs have no stamp, so both values are None there.
    The module is generated at packaging time, hence the dynamic import.
    """
    try:
        build_info = import_module("chipcompiler._build_info")
    except ImportError:
        return None, None
    return build_info.BUILD_COMMIT, build_info.BUILD_DATE


def build_channel() -> str | None:
    """Return the channel CI stamped into the bundle ("nightly", "dev", "stable"), if any."""
    try:
        build_info = import_module("chipcompiler._build_info")
    except ImportError:
        return None
    return getattr(build_info, "BUILD_CHANNEL", None) or None


def display_version() -> str:
    """Human-readable version that tells nightly/dev bundles apart from stable ones.

    The package version is identical for every build of a release, so non-stable
    stamped bundles append their channel, build date and short commit, e.g.
    ``0.1.0a12 (nightly 20261107 0da4cdb)``. ``ecc_version()`` stays the bare
    package version because update checks compare it against published releases.
    """
    version = ecc_version()
    channel = build_channel()
    if not channel or channel == "stable":
        return version
    commit, date = build_identity()
    details = " ".join(part for part in (channel, date, commit[:7] if commit else None) if part)
    return f"{version} ({details})"


def ecc_version() -> str:
    try:
        from chipcompiler import __version__
    except ImportError:
        fallback = None
    else:
        fallback = __version__
    return distribution_version("ecc", fallback=fallback)


def version_payload() -> dict[str, int | str | None]:
    build_commit, build_date = build_identity()
    return {
        "schema_version": VERSION_SCHEMA,
        "runtime": RUNTIME_LABEL,
        "ecc": ecc_version(),
        "dreamplace": distribution_version("ecc-dreamplace"),
        "ecc_tools": distribution_version("ecc-tools-bin"),
        "cli_contract": CLI_CONTRACT,
        "build_commit": build_commit,
        "build_date": build_date,
        "build_channel": build_channel(),
        "display_version": display_version(),
    }


def root_version_line() -> str:
    return f"ecc {display_version()}"


def version_text(payload: dict[str, int | str | None], tools: dict[str, str]) -> str:
    tool_lines = tuple(f"{name} {version}" for name, version in tools.items())
    return "\n".join(
        (
            f"ecc {payload.get('display_version') or payload['ecc']}",
            f"dreamplace {payload['dreamplace']}",
            f"ecc_tools {payload['ecc_tools']}",
            f"runtime {payload['runtime']}",
            *tool_lines,
        )
    )
