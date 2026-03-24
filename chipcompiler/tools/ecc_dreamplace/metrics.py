#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from chipcompiler.data import (
    Workspace, 
    WorkspaceStep, 
    StepMetrics, 
)

from chipcompiler.tools.ecc.subflow import EccSubFlow


def build_step_metrics(workspace: Workspace, 
                       step: WorkspaceStep,
                       subflow: EccSubFlow = None) -> StepMetrics:
    """
    Build and return a StepMetrics instance for the given workspace step.
    """
    from chipcompiler.tools.ecc import build_step_metrics as ecc_build_step_metrics
    return ecc_build_step_metrics(workspace=workspace,
                                  step=step,
                                  subflow=subflow)