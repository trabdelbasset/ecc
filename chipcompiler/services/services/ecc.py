#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import os

from chipcompiler.data import (
    create_workspace,
    load_workspace,
    StepEnum,
    StateEnum,
    PDK,
    get_pdk
)

from chipcompiler.engine import (
    EngineDB,
    EngineFlow
)

from chipcompiler.rtl2gds import build_rtl2gds_flow

from benchmark import  get_parameters

from chipcompiler.services.schemas import (
    CMDEnum,
    ECCRequest, 
    ECCResponse, 
    ResponseEnum,
    DATA_TEMPLATE
    )

class ECCService:
    def __init__(self):
        self.workspace = None
        self.engine_flow = None
        
    def check_cmd(self, request: ECCRequest, cmd : CMDEnum):
        # print cmd
        # print(request)
        
        # check cmd
        if request.cmd != cmd.value:
            response = ECCResponse(
                cmd=request.cmd,
                response=ResponseEnum.failed.value,
                data={},
                message = [].append(f"requese cmd not match {request.cmd}")
            )
            
            return False, response
        
        return True, None
    
    def __build_flow(self):
        engine_flow = EngineFlow(workspace=self.workspace)
        if not engine_flow.has_init():
            steps = build_rtl2gds_flow()
            for step, tool, state in steps:
                engine_flow.add_step(step=step, tool=tool, state=state)
        
        self.engine_flow = engine_flow
        
        if engine_flow.is_flow_success():
            return 
        engine_flow.create_step_workspaces()
    
    def create_workspace(self, request: ECCRequest) -> ECCResponse:
        # check cmd
        state, response = self.check_cmd(request, CMDEnum.create_workspace)
        if not state:
            return response 
            
        # get data
        data = request.data
 
        # check data
        
        # process cmd
        workspace = create_workspace(directory=data.get("directory", ""),
                                     pdk=data.get("pdk", ""),
                                     parameters=data.get("parameters", {}),
                                     origin_def=data.get("origin_def", ""),
                                     origin_verilog=data.get("origin_verilog", ""),
                                     input_filelist=data.get("rtl_list", ""))
        
        if workspace is None:
            return ECCResponse(
                cmd=request.cmd,
                response=ResponseEnum.failed.value,
                data={},
                message = [f"create workspace failed : {data.get('directory', '')}"]
            )
        else:
            self.workspace = workspace
            self.__build_flow()
            
            response_data = {
                "directory" : data.get("directory", "")
            }
            return ECCResponse(
                cmd=request.cmd,
                response=ResponseEnum.success.value,
                data=response_data,
                message = [f"create workspace success : {data.get('directory', '')}"]
            )
    
    def load_workspace(self, request: ECCRequest) -> ECCResponse:
        # check cmd
        state, response = self.check_cmd(request, CMDEnum.load_workspace)
        if not state:
            return response 
            
        # get data
        data = request.data
 
        # check data
        
        # process cmd
        workspace = load_workspace(directory=data.get("directory", ""))
        
        if workspace is None:
            return ECCResponse(
                cmd=request.cmd,
                response=ResponseEnum.failed.value,
                data={},
                message = [f"load workspace failed : {data.get('directory', '')}"]
            )
        else:
            self.workspace = workspace
            self.__build_flow()
            
            response_data = {
                "directory" : data.get("directory", "")
            }
            return ECCResponse(
                cmd=request.cmd,
                response=ResponseEnum.success.value,
                data=response_data,
                message = [f"load workspace success : {data.get('directory', '')}"]
            )
    
    def delete_workspace(self, request: ECCRequest) -> ECCResponse:
        # check cmd
        state, response = self.check_cmd(request, CMDEnum.delete_workspace)
        if not state:
            return response 
        
        # get data
        data = request.data
        directory = data.get('directory', '')
 
        # check data
        if self.workspace is None \
            or self.workspace.directory != directory \
                or not os.path.exists(directory):
            return ECCResponse(
                cmd=request.cmd,
                response=ResponseEnum.error.value,
                data={},
                message = [f"workspace not exist : {directory}"]
            )
            
        # process cmd
        self.engine_flow = None
        self.workspace = None
        try:
            import shutil
            shutil.rmtree(directory)
        except Exception as e:
            pass
            
        response_data = {
            "directory" : directory
        }
        return ECCResponse(
            cmd=request.cmd,
            response=ResponseEnum.success.value,
            data=response_data,
            message = [f"delete workspace success : {directory}"]
        )
        
    def rtl2gds(self, request: ECCRequest) -> ECCResponse:
        # check cmd
        state, response = self.check_cmd(request, CMDEnum.rtl2gds)
        if not state:
            return response 
        
        # get data
        data = request.data
        
        response_data = {
            "rerun" : data.get("rerun", False)
        }
 
        # check data
        if self.workspace is None \
            or not os.path.exists(self.workspace.directory):
            return ECCResponse(
                cmd=request.cmd,
                response=ResponseEnum.error.value,
                data=response_data,
                message = [f"workspace not exist : {self.workspace.directory}"]
            )
        
        if self.engine_flow is None:
            return ECCResponse(
                cmd=request.cmd,
                response=ResponseEnum.error.value,
                data=response_data,
                message = [f"rtl2gds flow not exist : {self.workspace.directory}"]
            )
            
        # process cmd
        try:
            if data.get("rerun", False):
                self.engine_flow.clear_states()
            self.engine_flow.run_steps()
        except Exception as e:
            pass
            
        return ECCResponse(
            cmd=request.cmd,
            response=ResponseEnum.success.value,
            data=response_data,
            message = [f"run rtl2gds success : {self.workspace.directory}"]
        )
        
    def run_step(self, request: ECCRequest) -> ECCResponse:
        # check cmd
        state, response = self.check_cmd(request, CMDEnum.run_step)
        if not state:
            return response 
        
        # get data
        data = request.data
        step = data.get("step", "")
        
        response_data = {
            "step" : step
        }
 
        # check data
        if self.workspace is None \
            or not os.path.exists(self.workspace.directory):
            return ECCResponse(
                cmd=request.cmd,
                response=ResponseEnum.error.value,
                data=response_data,
                message = [f"workspace not exist : {self.workspace.directory}"]
            )
            
        # process cmd
        state = StateEnum.Unstart
        try:
            state = self.engine_flow.run_step(step)
        except Exception as e:
            state = StateEnum.Imcomplete
            pass
        
        response_data["state"] = state.value
        
        if StateEnum.Success == state:
            return ECCResponse(
                cmd=request.cmd,
                response=ResponseEnum.success.value,
                data=response_data,
                message = [f"run step {step} success : {self.workspace.directory}"]
            )
        else:
            return ECCResponse(
                cmd=request.cmd,
                response=ResponseEnum.failed.value,
                data=response_data,
                message = [f"run step {step} failed with state {state.value} : {self.workspace.directory}"]
            )
            
            
