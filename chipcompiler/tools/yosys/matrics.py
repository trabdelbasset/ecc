#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from chipcompiler.data import Workspace, WorkspaceStep, StepMetrics, load_metrics, save_metrics

def build_step_metrics(workspace: Workspace, 
                       step: WorkspaceStep) -> StepMetrics:
    """
    Build and return a StepMetrics instance for the given workspace step.
    """
    step_metrics = StepMetrics()
    step_metrics.path = step.analysis['metrics']    
    
    metrics_summary = {}
    metrics_summary['step'] = step.name
    metrics_summary['tool'] = step.tool
    
    
    step_metrics.data = metrics_summary
        
    return step_metrics