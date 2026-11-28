import os
from typing import Any

import pytest

from chipcompiler.analysis.qor.loader import load_workspace_qor_inputs
from test.analysis.qor.helpers import (
    FULL_FLOW,
    loader_metric,
    make_loader_workspace,
    write_step_payload,
)


class TestGateEvidence:
    """Gate metrics require an existing evidence artifact no newer than qor_metrics.json."""

    def _workspace(self, tmp_path):
        workspace = make_loader_workspace(tmp_path, FULL_FLOW)
        write_step_payload(
            workspace.directory,
            "drc_ecc",
            [
                loader_metric(
                    "drc_count", 0, project_role="gate", source={"path": "feature/drc.step.json"}
                ),
                loader_metric(
                    "drc_trend", 5, project_role="trend", source={"path": "feature/gone.json"}
                ),
            ],
        )
        evidence = os.path.join(workspace.directory, "drc_ecc", "feature", "drc.step.json")
        os.makedirs(os.path.dirname(evidence), exist_ok=True)
        with open(evidence, "w") as f:
            f.write("{}")
        cache = os.path.join(workspace.directory, "drc_ecc", "analysis", "qor_metrics.json")
        return workspace, evidence, cache

    def test_present_and_older_evidence_keeps_gate_metric(self, tmp_path):
        workspace, evidence, cache = self._workspace(tmp_path)
        mtime = os.stat(cache).st_mtime - 10
        os.utime(evidence, (mtime, mtime))
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_count") == 0
        assert not inputs.config_warnings

    def test_missing_evidence_drops_gate_metric(self, tmp_path):
        workspace, evidence, _ = self._workspace(tmp_path)
        os.remove(evidence)
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_count") is None
        assert any("drc_count" in w and "missing" in w for w in inputs.config_warnings)

    def test_evidence_newer_than_cache_drops_gate_metric(self, tmp_path):
        workspace, evidence, cache = self._workspace(tmp_path)
        mtime = os.stat(cache).st_mtime + 60
        os.utime(evidence, (mtime, mtime))
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_count") is None
        assert any("stale" in w for w in inputs.config_warnings)

    def test_small_mtime_skew_is_tolerated(self, tmp_path):
        workspace, evidence, cache = self._workspace(tmp_path)
        mtime = os.stat(cache).st_mtime + 0.5
        os.utime(evidence, (mtime, mtime))
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_count") == 0

    def test_missing_source_path_drops_gate_metric(self, tmp_path):
        workspace, _, _ = self._workspace(tmp_path)
        write_step_payload(
            workspace.directory,
            "drc_ecc",
            [loader_metric("drc_count", 0, project_role="gate", source={})],
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_count") is None

    @pytest.mark.parametrize("bad_rel", ["/etc/passwd", "../outside.json"])
    def test_evidence_path_escape_drops_gate_metric(self, tmp_path, bad_rel):
        workspace, _, _ = self._workspace(tmp_path)
        (tmp_path / "outside.json").write_text("{}")
        write_step_payload(
            workspace.directory,
            "drc_ecc",
            [loader_metric("drc_count", 0, project_role="gate", source={"path": bad_rel})],
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_count") is None
        assert any("invalid evidence path" in w for w in inputs.config_warnings)

    def test_non_gate_metrics_are_not_checked(self, tmp_path):
        workspace, _, _ = self._workspace(tmp_path)
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.value("drc_trend") == 5
