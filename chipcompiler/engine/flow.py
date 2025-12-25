#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from chipcompiler.data import Workspace, WorkspaceStep
from chipcompiler.data import StateEnum, StepEnum

class EngineFlow:
    def __init__(self, workspace : Workspace):
        self.workspace = workspace
        self.workspace_steps = []
      
        self.load()
    
    def build_default_steps(self):
        # Flow step sequences
        steps = []

        steps.append(self.init_step(StepEnum.SYNTHESIS, "yosys", StateEnum.Unstart))
        steps.append(self.init_step(StepEnum.FLOORPLAN, "iEDA", StateEnum.Unstart))
        steps.append(self.init_step(StepEnum.PLACEMENT, "iEDA", StateEnum.Unstart))
        steps.append(self.init_step(StepEnum.CTS, "iEDA", StateEnum.Unstart))
        steps.append(self.init_step(StepEnum.LEGALIZATION, "iEDA", StateEnum.Unstart))
        steps.append(self.init_step(StepEnum.ROUTING, "iEDA", StateEnum.Unstart))
        steps.append(self.init_step(StepEnum.FILLER, "iEDA", StateEnum.Unstart))
        steps.append(self.init_step(StepEnum.GDS, "klayout", StateEnum.Ignored))
        steps.append(self.init_step(StepEnum.SIGNOFF, "innovus", StateEnum.Ignored))
        
        self.workspace.flow.data = {"steps" : steps}
        
        self.save()
    
    def init_step(self,
                  step : StepEnum | str,
                  tool : str,
                  state : str | StateEnum):
        step_value = step.value if isinstance(step, StepEnum) else step
        state_value = state.value if isinstance(state, StateEnum) else state
        return {
            "name" : step_value, # step name
            "tool" : tool, # eda tool name
            "state" : state_value, # step state
            "runtime" : "", # step run time
            "info" : {} # step additional infomation
        }
    
    def load(self) -> bool:
        from chipcompiler.utility import json_read
        self.workspace.flow.data = json_read(self.workspace.flow.path)
        if len(self.workspace.flow.data.get("steps", [])) <= 0:
            return False

        return True
        
    def save(self) -> bool:
        from chipcompiler.utility import json_write
        return json_write(self.workspace.flow.path, 
                          self.workspace.flow.data)
        
    def get_step(self,
                 name : str,
                 tool : str):
        for step in self.workspace.flow.data.get("steps", []):
            if step.get("name") == name and step.get("tool") == tool:
                return step
        
        return None
    
    def check_state(self,
                   name : str,
                   tool : str,
                   state : str):
        """
        return True if step state has been set
        """
        step = self.get_step(name, tool)
        if step is not None \
            and step.get("state") == state:
            return True
            
        return False
        
    def set_state(self, 
                 name : str,
                 tool : str,
                 state : str) -> bool:
        for step in self.workspace.flow.data.get("steps", []):
            if step.get("name") == name and step.get("tool") == tool:
                step["state"] = state
                
                self.save()
                return True
            
        return False
    
    def clear_states(self):
        from chipcompiler.data import StateEnum
        for step in self.workspace.flow.data.get("steps", []):
            step["state"] = StateEnum.Unstart.value
            
        self.save()
        
    def is_flow_success(self):
        """
        check all steps success
        """
        from chipcompiler.data import StateEnum
        for step in self.workspace.flow.data.get("steps", []):
            if(step["state"] != StateEnum.Success.value):
                return False
            
        return True
    
    def create_step_workspaces(self):
        """
        create all step workspaces
        """
        pre_step = None
        for step in self.workspace.flow.data.get("steps", []):
            if pre_step is None:
                # use the origin def and verilog in workspace for the first step.
                input_def = self.workspace.design.origin_def
                input_verilog = self.workspace.design.origin_verilog
            else:
                # use the output def and verilog from last step.
                input_def = pre_step.output["def"]
                input_verilog = pre_step.output["verilog"]
                
            from chipcompiler.tools import create_step, run_step
            # create workspace step
            eda_step = create_step(workspace=self.workspace,
                                   step=step["name"],
                                   eda=step["tool"],
                                   input_def=input_def,
                                   input_verilog=input_verilog)
    
    def run_steps(self) -> bool:
        """
        run all flow steps
        """
        pre_step = None
        for step in self.workspace.flow.data.get("steps", []):
            if pre_step is None:
                # use the origin def and verilog in workspace for the first step.
                input_def = self.workspace.design.origin_def
                input_verilog = self.workspace.design.origin_verilog
            else:
                # use the output def and verilog from last step.
                input_def = pre_step.output["def"]
                input_verilog = pre_step.output["verilog"]
                
            state = self.run_step(step=step["name"],
                                  tool=step["tool"],
                                  input_def=input_def,
                                  input_verilog=input_verilog)
            
            match(state):
                case StateEnum.Success:
                    pre_step = step
                    continue
                case StateEnum.Ignored:
                    continue
                case StateEnum.Invalid:
                    return False
                case StateEnum.Unstart:
                    return False
                case StateEnum.Imcomplete:
                    return False
                case StateEnum.Pending:
                    return False
                case StateEnum.Ongoing:
                    return False
        
        return True
            
    def run_step(self,
                 step : str,
                 tool : str,
                 input_def : str,
                 input_verilog : str) -> StateEnum:
        """
        run single step
        """
        from chipcompiler.tools import create_step, run_step
        # create workspace step
        eda_step = create_step(workspace=self.workspace,
                               step=step,
                               eda=tool,
                               input_def=input_def,
                               input_verilog=input_verilog)
        
        # save workspace step
        self.workspace_steps.append(eda_step)
        
        # run steps
        state = run_step(self.workspace, eda_step)
        
        # save state
        self.set_state(name=step,
                       tool=tool,
                       state=state.value)
        
        return state