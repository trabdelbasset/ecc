#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os
       
from chipcompiler.data import WorkspaceStep, Workspace, StateEnum, StepEnum
from chipcompiler.tools.iEDA.module import IEDAModule
from chipcompiler.tools.iEDA.utility import is_eda_exist

def create_db_engine(workspace: Workspace,
                     step: WorkspaceStep) -> IEDAModule:
    """"""
    if not is_eda_exist():
        return False
    
    from chipcompiler.tools.iEDA.module import IEDAModule
    eda_inst = IEDAModule()
    
    eda_inst.init_config(flow_config=step.config["flow"],
                         db_config=step.config["db"],
                         output_dir=step.data["dir"],
                         feature_dir=step.feature["dir"])
    
    eda_inst.init_techlef(workspace.pdk.tech)
    eda_inst.init_lefs(workspace.pdk.lefs)
    
    # if db def exist, read db def
    if os.path.exists(step.input["def"]):
        eda_inst.read_def(step.input["def"])      
    else:
        #else, read step output verilog
        if os.path.exists(step.input["verilog"]):
            eda_inst.read_verilog(verilog=step.input["verilog"],
                                  top_module=workspace.design.top_module)
        else:
            return None
    
    return eda_inst

def get_eda_instance(workspace: Workspace,
                 step: WorkspaceStep,
                 instance: IEDAModule=None) -> IEDAModule:
    """
    module is iEDA module from db engine, 
    eda instacnce may initialize data from this module if module has been set
    """
    eda_inst = None
    if instance is not None:
        # copy data from module, but not set module to eda inst
        # TBD
        eda_inst = instance
    else:
        # init iEDA module
        eda_inst = create_db_engine(workspace=workspace,
                                    step=step)
    
    return eda_inst

def save_data(step: WorkspaceStep,
              module : IEDAModule) -> bool:
    """
    module is iEDA module from db engine, 
    eda instacnce may initialize data from this module if module has been set
    """
    if module is None:
        return FALSE
    
    module.def_save(def_path=step.output["def"])
    module.verilog_save(output_verilog=step.output["verilog"])
    module.feature_sammry(json_path=step.feature["db"])
    module.feature_step(step=step.name,
                        json_path=step.feature["step"])
    
    module.report_summary(path=step.report["summary"])
    
    return True
    
def run_step(workspace: Workspace,
             step: WorkspaceStep,
             module : IEDAModule = None) -> bool:
    if not is_eda_exist():
        return StateEnum.Invalid
        
    state = False
    match(step.name):
        case StepEnum.NETLIST_OPT.value:
            state = run_net_opt(workspace=workspace, 
                                step=step, 
                                module=module)
        case StepEnum.PLACEMENT.value:
            state = run_placement(workspace=workspace, 
                                  step=step, 
                                  module=module)
        case StepEnum.CTS.value:
            state = run_cts(workspace=workspace, 
                            step=step, 
                            module=module)
        case StepEnum.TIMING_OPT_DRV.value:
            state = run_timing_opt_drv(workspace=workspace, 
                                       step=step, 
                                       module=module)
        case StepEnum.TIMING_OPT_HOLD.value:
            state = run_timing_opt_hold(workspace=workspace, 
                                        step=step, 
                                        module=module)
        case StepEnum.LEGALIZATION.value:
            state = run_legalization(workspace=workspace, 
                                     step=step, 
                                     module=module)
        case StepEnum.ROUTING.value:
            state = run_routing(workspace=workspace, 
                                step=step, 
                                module=module)
        case StepEnum.FILLER.value:
            state = run_filler(workspace=workspace, 
                               step=step, 
                               module=module)
            
    return state

def run_net_opt(workspace: Workspace,
                step: WorkspaceStep,
                module : IEDAModule = None) -> bool:
    """
    run net optimization
    """
    eda_inst = get_eda_instance(workspace=workspace,
                                step=step,
                                instance=module)
    if eda_inst is not None:
        eda_inst.run_net_opt(config=step.config[f"{StepEnum.NETLIST_OPT.value}"])
        
        return save_data(step=step, module=eda_inst)
    
    return False
    
def run_placement(workspace: Workspace,
                  step: WorkspaceStep,
                  module : IEDAModule = None) -> bool:
    """
    run placement
    """
    eda_inst = get_eda_instance(workspace=workspace,
                                step=step,
                                instance=module)
    
    if eda_inst is not None:
        eda_inst.run_placement(config=step.config[f"{StepEnum.PLACEMENT.value}"])
        
        return save_data(step=step, module=eda_inst)
    
    return False

def run_cts(workspace: Workspace,
            step: WorkspaceStep,
            module : IEDAModule = None) -> bool:
    """
    run CTS
    """
    eda_inst = get_eda_instance(workspace=workspace,
                                step=step,
                                instance=module)
    
    if eda_inst is not None:
        eda_inst.run_cts(config=step.config[f"{StepEnum.CTS.value}"],
                         output=step.data[f"{StepEnum.CTS.value}"])
        
        eda_inst.report_cts(output=step.data[f"{StepEnum.CTS.value}"])
        
        eda_inst.run_legalize(config=step.config[f"{StepEnum.LEGALIZATION.value}"])
        
        eda_inst.feature_cts_map(json_path=step.feature["map"])
        
        return save_data(step=step, module=eda_inst)
    
    return False

def run_timing_opt_drv(workspace: Workspace,
                       step: WorkspaceStep,
                       module : IEDAModule = None) -> bool:
    """
    run timing optization drv
    """
    eda_inst = get_eda_instance(workspace=workspace,
                                step=step,
                                instance=module)
    
    if eda_inst is not None:
        eda_inst.run_timing_opt_drv(config=step.config[f"{StepEnum.TIMING_OPT_DRV.value}"])
        
        return save_data(step=step, module=eda_inst)
    
    return False

def run_timing_opt_hold(workspace: Workspace,
                        step: WorkspaceStep,
                        module : IEDAModule = None) -> bool:
    """
    run timing optization hold 
    """
    eda_inst = get_eda_instance(workspace=workspace,
                                step=step,
                                instance=module)
    
    if eda_inst is not None:
        eda_inst.run_timing_opt_hold(config=step.config[f"{StepEnum.TIMING_OPT_HOLD.value}"])
        
        return save_data(step=step, module=eda_inst)
    
    return False

def run_routing(workspace: Workspace,
                step: WorkspaceStep,
                module : IEDAModule = None) -> bool:
    """
    run routing
    """
    eda_inst = get_eda_instance(workspace=workspace,
                                step=step,
                                instance=module)
    
    
    if eda_inst is not None:
        if eda_inst.is_rt_timing_enable(config=step.config[f"{StepEnum.ROUTING.value}"]):
            eda_inst.init_sta(output_dir=step.data["sta"],
                              design=workspace.design.name,
                              lib_paths=workspace.pdk.libs,
                              sdc_path=workspace.pdk.sdc)
            
        eda_inst.run_routing(config=step.config[f"{StepEnum.ROUTING.value}"])
        
        return save_data(step=step, module=eda_inst)
    
    return False

def run_legalization(workspace: Workspace,
                     step: WorkspaceStep,
                     module : IEDAModule = None) -> bool:
    """
    run placement legalization
    """
    eda_inst = get_eda_instance(workspace=workspace,
                                step=step,
                                instance=module)
    
    if eda_inst is not None:
        eda_inst.run_legalize(config=step.config[f"{StepEnum.LEGALIZATION.value}"])
        
        return save_data(step=step, module=eda_inst)
    
    return False

def run_filler(workspace: Workspace,
               step: WorkspaceStep,
               module : IEDAModule = None) -> bool:
    """
    run placement filler
    """
    eda_inst = get_eda_instance(workspace=workspace,
                                step=step,
                                instance=module)
    
    if eda_inst is not None:
        eda_inst.run_filler(config=step.config[f"{StepEnum.FILLER.value}"])
        
        return save_data(step=step, module=eda_inst)
    
    return False