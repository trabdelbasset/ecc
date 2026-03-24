#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import os
from chipcompiler.data import (
    Workspace, 
    WorkspaceStep, 
    StepEnum
)

    
def get_step_info(workspace: Workspace, 
                  step: WorkspaceStep,
                  id : str) -> dict:
    """
    get step info by step and command id, return dict as resource definition
    """
    from chipcompiler.tools.ecc import get_step_info as ecc_get_step_info
    step_info = {}
    

    step_info = ecc_get_step_info(workspace=workspace,
                                  step=step,
                                  id=id)
    
    return step_info