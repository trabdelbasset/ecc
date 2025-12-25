#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from dataclasses import dataclass, field
from .parameter import Parameters, save_parameter
    
@dataclass
class PDK:
    """
    Dataclass for PDK information
    """
    name : str = "" # pdk name
    version : str = "" # pdk version
    tech : str = "" # pdk tech lef file
    lefs : list = field(default_factory=list) # pdk lef files
    libs : list = field(default_factory=list) # pdk liberty files
    sdc : str = "" # pdk sdc file
    spef : str = "" # pdk spef file

@dataclass
class OriginDesign:
    """
    Dataclass for original design information
    """
    name : str = "" # design name
    top_module : str = "" # top module name
    origin_def : str = "" # original def file path
    origin_verilog : str = "" # original verilog file path
    
@dataclass
class Flow:
    """
    Dataclass for design flow
    """
    path : str = "" # flow file path
    data : dict = field(default_factory=dict) # flow steps
    
@dataclass
class Workspace:
    """
    Dataclass for workspace information
    """
    directory : str = "" # workspace directory
    design : OriginDesign = field(default_factory=OriginDesign) # original design info
    pdk : PDK = field(default_factory=PDK) # pdk information
    parameters : Parameters = field(default_factory=Parameters) # design parameters
    flow : Flow = field(default_factory=Flow) # design flow for this workspace
    
@dataclass
class WorkspaceStep:
    """
    Dataclass for workspace step path information, describe all the info for this task step.
    """
    # step basic info
    name : str = "" # step name
    directory : str = "" # step working directory
    
    # eda tool info
    tool : str = "" # eda tool name
    version : str = "" # eda tool version
    
    # Paths for this step
    config : dict = field(default_factory=dict) # config path about this step
    input : dict = field(default_factory=dict) # input path about this step
    output : dict = field(default_factory=dict) # output path about this step
    data : dict = field(default_factory=dict) # data path about this step
    feature : dict = field(default_factory=dict) # features path about this step
    report : dict = field(default_factory=dict) # report path about this step
    log : dict = field(default_factory=dict) # log path about this step
    script : dict = field(default_factory=dict) # script path about this step
    analysis : dict = field(default_factory=dict) # analysis path about this step
    
    # step result info
    result : dict = field(default_factory=dict) # result info about this step


def create_workspace(directory : str,
                     origin_def : str,
                     origin_verilog : str,
                     pdk : PDK,
                     parameters : Parameters) -> Workspace:
    # create workspace directory
    import os
    os.makedirs(directory, exist_ok=True)
    
    # create workspace instance
    workspace = Workspace()
    
    #update config
    workspace.design.name = parameters.data["Design"]
    workspace.design.top_module = parameters.data["Top module"]         
    workspace.pdk = pdk
    workspace.parameters = parameters
    
    # update path
    workspace.directory = directory
    workspace.parameters.path = f"{directory}/parameters.json"
    workspace.flow.path = f"{directory}/flow.json"
    
    # update orign files to workspace origin folder
    import shutil
    os.makedirs(f"{directory}/origin", exist_ok=True)
    if os.path.exists(origin_def):
        shutil.copy(origin_def, f"{directory}/origin/{os.path.basename(origin_def)}")
        workspace.design.origin_def = f"{directory}/origin/{os.path.basename(origin_def)}"
    if os.path.exists(origin_verilog):
        shutil.copy(origin_verilog, f"{directory}/origin/{os.path.basename(origin_verilog)}")
        workspace.design.origin_verilog = f"{directory}/origin/{os.path.basename(origin_verilog)}"
    if os.path.exists(pdk.sdc):
        shutil.copy(pdk.sdc, f"{directory}/origin/{os.path.basename(pdk.sdc)}")
        workspace.pdk.sdc = f"{directory}/origin/{os.path.basename(pdk.sdc)}"
    if os.path.exists(pdk.spef):
        shutil.copy(pdk.spef, f"{directory}/origin/{os.path.basename(pdk.spef)}")
        workspace.pdk.spef = f"{directory}/origin/{os.path.basename(pdk.spef)}"
    
    # save parameter
    save_parameter(workspace.parameters)
     
    return workspace