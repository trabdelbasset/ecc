#!/usr/bin/env python
import os
from pathlib import Path
from types import SimpleNamespace

from chipcompiler.tools.yosys import utility


def _create_oss_cad_tree(base_dir: Path) -> tuple[Path, Path]:
    """Create a minimal OSS CAD directory layout for testing."""
    oss_path = base_dir / "oss-cad-suite"
    bin_dir = oss_path / "bin"
    bin_dir.mkdir(parents=True)

    yosys_name = "yosys.exe" if utility.os.name == "nt" else "yosys"
    yosys_bin = bin_dir / yosys_name
    yosys_bin.write_text("")

    share_dir = oss_path / "share" / "yosys"
    (share_dir / "plugins").mkdir(parents=True)
    (share_dir / "techlibs").mkdir(parents=True)

    return oss_path, yosys_bin


def test_get_yosys_command_prefers_oss_cad_without_mutating_environ(tmp_path, monkeypatch):
    oss_path, yosys_bin = _create_oss_cad_tree(tmp_path)

    monkeypatch.setenv("CHIPCOMPILER_OSS_CAD_DIR", str(oss_path))
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.delenv("YOSYS_PLUGINPATH", raising=False)
    monkeypatch.delenv("YOSYS_DATDIR", raising=False)

    before = {k: os.environ.get(k) for k in ["PATH", "YOSYS_PLUGINPATH", "YOSYS_DATDIR"]}
    command = utility.get_yosys_command()
    after = {k: os.environ.get(k) for k in ["PATH", "YOSYS_PLUGINPATH", "YOSYS_DATDIR"]}

    assert command == [str(yosys_bin)]
    assert before == after


def test_get_yosys_command_returns_empty_when_not_found(monkeypatch):
    monkeypatch.delenv("CHIPCOMPILER_OSS_CAD_DIR", raising=False)
    monkeypatch.setattr(utility.shutil, "which", lambda _: None)

    assert utility.get_yosys_command() == []


def test_get_yosys_runtime_builds_local_env_without_mutating_global_env(tmp_path, monkeypatch):
    oss_path, yosys_bin = _create_oss_cad_tree(tmp_path)

    monkeypatch.setenv("CHIPCOMPILER_OSS_CAD_DIR", str(oss_path))
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.delenv("YOSYS_PLUGINPATH", raising=False)
    monkeypatch.delenv("YOSYS_DATDIR", raising=False)

    before = {k: os.environ.get(k) for k in ["PATH", "YOSYS_PLUGINPATH", "YOSYS_DATDIR"]}
    command, env = utility.get_yosys_runtime()
    after = {k: os.environ.get(k) for k in ["PATH", "YOSYS_PLUGINPATH", "YOSYS_DATDIR"]}

    expected_prefix = str(oss_path / "bin") + os.pathsep
    assert command == [str(yosys_bin)]
    assert env["PATH"].startswith(expected_prefix)
    assert env["YOSYS_PLUGINPATH"] == str(oss_path / "share" / "yosys" / "plugins")
    assert env["YOSYS_DATDIR"] == str(oss_path / "share" / "yosys")
    assert before == after


def test_check_slang_support_accepts_builtin_frontend(tmp_path, monkeypatch):
    log_path = tmp_path / "check.log"
    calls = []

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        calls.append(
            {
                "cmd": list(cmd),
                "cwd": cwd,
                "env": env,
                "timeout": timeout,
            }
        )
        return SimpleNamespace(returncode=0, stdout=b"read_slang [options] [filename]")

    monkeypatch.setattr(utility.subprocess, "run", fake_run)
    with open(log_path, "w") as log_file:
        ok = utility.check_slang_support(
            yosys_cmd=["yosys"],
            cwd_dir="/tmp/test",
            yosys_env={"PATH": "/tmp/bin"},
            log_file=log_file,
        )

    assert ok is True
    assert len(calls) == 1
    assert calls[0]["cmd"] == ["yosys", "-Q", "-T", "-p", "help read_slang"]
    assert calls[0]["cwd"] == "/tmp/test"
    assert calls[0]["env"] == {"PATH": "/tmp/bin"}
    assert calls[0]["timeout"] == 60


def test_check_slang_support_falls_back_to_plugin(tmp_path, monkeypatch):
    log_path = tmp_path / "check.log"
    calls = []

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        calls.append(list(cmd))
        if "help read_slang" in cmd:
            return SimpleNamespace(returncode=0, stdout=b"No such command or cell type: read_slang")
        return SimpleNamespace(returncode=0, stdout=b"")

    monkeypatch.setattr(utility.subprocess, "run", fake_run)
    with open(log_path, "w") as log_file:
        ok = utility.check_slang_support(
            yosys_cmd=["yosys"],
            cwd_dir="/tmp/test",
            yosys_env={"PATH": "/tmp/bin"},
            log_file=log_file,
        )

    assert ok is True
    assert calls == [
        ["yosys", "-Q", "-T", "-p", "help read_slang"],
        ["yosys", "-Q", "-T", "-p", "plugin -i slang"],
    ]


def test_check_slang_support_writes_error_on_failure(tmp_path, monkeypatch):
    log_path = tmp_path / "check_fail.log"

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        if "help read_slang" in cmd:
            return SimpleNamespace(returncode=0, stdout=b"No such command or cell type: read_slang")
        return SimpleNamespace(returncode=1, stdout=b"")

    monkeypatch.setattr(utility.subprocess, "run", fake_run)
    with open(log_path, "w") as log_file:
        ok = utility.check_slang_support(
            yosys_cmd=["yosys"],
            cwd_dir="/tmp/test",
            yosys_env={"PATH": "/tmp/bin"},
            log_file=log_file,
        )

    assert ok is False
    assert "slang frontend check failed" in log_path.read_text()


def test_extract_and_parse_yosys_version():
    assert utility.extract_yosys_version_token("Yosys 0.70+16 (git sha1 3bb533450)") == "0.70+16"
    assert utility.extract_yosys_version_token("0.68+132") == "0.68+132"
    assert utility.parse_yosys_version("Yosys 0.70+16 (git sha1 3bb533450)") == (0, 70)
    assert utility.parse_yosys_version("0.67") == (0, 67)
    assert utility.parse_yosys_version("0.66+99") == (0, 66)
    assert utility.parse_yosys_version("Yosys unknown-dev") is None
    assert utility.parse_yosys_version("unrecognized") is None


def test_check_yosys_version_accepts_min_and_newer(monkeypatch):
    for banner, expected_ver in (
        ("Yosys 0.67 (git sha1 abcdef)", "0.67"),
        ("Yosys 0.70+16 (git sha1 3bb533450, Release)", "0.70+16"),
    ):
        monkeypatch.setattr(
            utility.subprocess,
            "run",
            lambda *_a, _b=banner, **_k: SimpleNamespace(returncode=0, stdout=_b.encode()),
        )
        ok, version_str, err = utility.check_yosys_version(["yosys"], {})
        assert ok is True
        assert version_str == expected_ver
        assert err == ""


def test_check_yosys_version_rejects_old_failed_or_unparseable(monkeypatch):
    monkeypatch.setattr(
        utility.subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(returncode=0, stdout=b"Yosys 0.66+99 (git sha1 old)"),
    )
    ok, version_str, err = utility.check_yosys_version(["yosys"], {})
    assert ok is False
    assert version_str == "0.66+99"
    assert "0.66+99" in err
    assert ">= 0.67" in err

    monkeypatch.setattr(
        utility.subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(returncode=1, stdout=b""),
    )
    ok, version_str, err = utility.check_yosys_version(["yosys"], {})
    assert ok is False
    assert version_str is None
    assert "Could not determine Yosys version" in err

    monkeypatch.setattr(
        utility.subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(returncode=0, stdout=b"Yosys dev-custom"),
    )
    ok, version_str, err = utility.check_yosys_version(["yosys"], {})
    assert ok is False
    assert version_str == "dev-custom"
    assert "Unrecognized Yosys version" in err
