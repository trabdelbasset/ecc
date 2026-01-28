#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from chipcompiler.data import (
    Workspace, 
    WorkspaceStep, 
)

from chipcompiler.tools.ecc.metrics import build_step_metrics
    
def get_step_info(workspace: Workspace, 
                  step: WorkspaceStep,
                  id : str) -> dict:
    """
    get step info by step and command id, return dict as resource definition
    """
    step_info = {}
    
    match id:
        case "views":
            step_info = build_views(workspace=workspace, step=step)
        case "layout":
            step_info = build_layout(workspace=workspace, step=step)
        case "metrics":
            step_info = build_metrics(workspace=workspace, step=step)
        case "subflow":
            step_info = build_subflow(workspace=workspace, step=step)

    return step_info

def build_metrics(workspace: Workspace, 
                  step: WorkspaceStep) -> dict:
    metrics = build_step_metrics(workspace=workspace,
                                 step=step)
    info = {
        "metrics" : metrics.path
    }
    
    return info

def build_layout(workspace: Workspace, 
                 step: WorkspaceStep) -> dict:
    info = {
        "image" : step.output.get("image", "")
    }
    
    return info

def build_views(workspace: Workspace, 
                step: WorkspaceStep) -> dict:
    metrics = build_step_metrics(workspace=workspace,
                                 step=step)
    
    info = {
        "image" : step.output.get("image", ""),
        "metrics" : metrics.path,
        "information" : {}
    }
    
    return info

def build_subflow(workspace: Workspace, 
                  step: WorkspaceStep) -> dict:       
    info = {
        "path" : step.subflow.get("path", "")
    }
    
    return info