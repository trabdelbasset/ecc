import json
from pathlib import Path
from typing import Any

import pytest

from chipcompiler.analysis.qor.loader import load_workspace_qor_inputs
from test.analysis.qor.helpers import (
    SUCCESS,
    loader_metric,
    make_loader_workspace,
    write_step_payload,
)


class TestEgrOverflowGrid:
    def _detail(
        self,
        *,
        available: Any = True,
        value_count: Any = 8,
        nonzero_count: Any = 2,
        source_file: str = "feature/egr_congestion_map/place_egr_union_overflow.csv",
        feature_source_path: str = "feature/placement.map.json",
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "place_map_metrics",
                "presentation": "place_map_summary",
                "summary": {
                    "maps": [
                        {
                            "group": "density",
                            "metric": "allcell",
                            "available": True,
                            "value_count": 4,
                            "nonzero_count": 1,
                        },
                        {
                            "group": "congestion",
                            "metric": "egr",
                            "direction": "union",
                            "source_file": source_file,
                            "available": available,
                            "value_count": value_count,
                            "nonzero_count": nonzero_count,
                        },
                    ]
                },
                "feature_source": {"kind": "feature", "path": feature_source_path, "selector": ""},
            }
        ]

    def _workspace(self, tmp_path, *, placement_state=SUCCESS, details=None):
        workspace = make_loader_workspace(tmp_path, {"placement": placement_state})
        if placement_state == SUCCESS:
            write_step_payload(
                workspace.directory,
                "placement_dreamplace",
                [loader_metric("probe_metric", 1.0)],
                details=details,
            )
        return workspace

    def test_reads_persisted_place_map_metrics(self, tmp_path):
        workspace = self._workspace(tmp_path, details=self._detail())
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.egr_gcell_count == 8
        assert inputs.egr_overflowed_gcell_count == 2
        assert (
            inputs.egr_grid_source_path == "feature/egr_congestion_map/place_egr_union_overflow.csv"
        )

    def test_falls_back_to_feature_source_when_map_source_file_empty(self, tmp_path):
        workspace = self._workspace(tmp_path, details=self._detail(source_file=""))
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.egr_gcell_count == 8
        assert inputs.egr_overflowed_gcell_count == 2
        assert inputs.egr_grid_source_path == "feature/placement.map.json"

    def test_consumes_metrics_emitted_by_placement_extractor_without_rereading_csv(self, tmp_path):
        from chipcompiler.data import OriginDesign, StepEnum, Workspace
        from chipcompiler.tools.ecc.builder import build_step, build_step_space
        from chipcompiler.tools.ecc.metrics import build_metrics_placement

        workspace_stub = make_loader_workspace(tmp_path, {"placement": SUCCESS})
        ws_root = Path(workspace_stub.directory)
        real_ws = Workspace(directory=ws_root, design=OriginDesign(name="gcd", top_module="gcd"))
        step = build_step(
            workspace=real_ws,
            step_name=StepEnum.PLACEMENT.value,
            step_directory=ws_root / "placement_dreamplace",
            input_def=ws_root / "input.def",
            input_verilog=ws_root / "input.v",
        )
        build_step_space(step)
        assert step.feature.dir is not None
        assert step.feature.map is not None
        csv_dir = step.feature.dir / "egr_congestion_map"
        csv_dir.mkdir(parents=True, exist_ok=True)
        egr_csv = csv_dir / "place_egr_union_overflow.csv"
        egr_csv.write_text("0,0,3,0\n0,1,0,0\n", encoding="utf-8")
        step.feature.map.write_text(
            json.dumps(
                {
                    "Congestion": {
                        "map": {"egr": {"union": str(egr_csv)}},
                        "overflow": {"total": {"union": 4}, "max": {"union": 3}},
                    }
                }
            ),
            encoding="utf-8",
        )
        assert build_metrics_placement(real_ws, step) is not None
        # Prove loader relies strictly on persisted qor_metrics.json stats, not the CSV file.
        egr_csv.unlink()

        inputs: Any = load_workspace_qor_inputs(workspace_stub)
        assert inputs.egr_gcell_count == 8
        assert inputs.egr_overflowed_gcell_count == 2
        assert inputs.egr_grid_source_path is not None
        assert inputs.egr_grid_source_path.endswith("place_egr_union_overflow.csv")

    @pytest.mark.parametrize(
        "overrides",
        [
            {"available": False},
            {"value_count": 0},
            {"nonzero_count": -1},
            {"nonzero_count": 9, "value_count": 8},
            {"value_count": True},
            {"nonzero_count": True},
        ],
    )
    def test_invalid_or_unavailable_persisted_stats_leave_grid_unknown(self, tmp_path, overrides):
        workspace = self._workspace(tmp_path, details=self._detail(**overrides))
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.egr_gcell_count is None
        assert inputs.egr_overflowed_gcell_count is None

    def test_missing_place_map_detail_leaves_grid_unknown(self, tmp_path):
        inputs: Any = load_workspace_qor_inputs(
            make_loader_workspace(tmp_path, {"placement": SUCCESS})
        )
        assert inputs.egr_gcell_count is None
        assert inputs.egr_overflowed_gcell_count is None

    def test_non_success_placement_leaves_grid_unknown(self, tmp_path):
        workspace = self._workspace(tmp_path, placement_state="Unstart")
        write_step_payload(
            workspace.directory,
            "placement_dreamplace",
            [loader_metric("probe_metric", 1.0)],
            details=self._detail(),
        )
        inputs: Any = load_workspace_qor_inputs(workspace)
        assert inputs.egr_gcell_count is None
        assert inputs.egr_overflowed_gcell_count is None
