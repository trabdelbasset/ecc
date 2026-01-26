#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import os

current_dir = os.path.split(os.path.abspath(__file__))[0]
root = current_dir.rsplit('/', 1)[0]
sys.path.append(root)

from chipcompiler.data import (
    create_workspace,
    log_workspace,
    StepEnum,
    StateEnum,
    get_pdk
)

from chipcompiler.engine import (
    EngineDB,
    EngineFlow
)

from chipcompiler.services import (
    ECCService,
    ecc_service,
    ECCRequest,
    ECCResponse
)

from benchmark import get_parameters

def test_sky130_gcd():
    workspace_dir="{}/test/examples/sky130_gcd".format(root)

    input_def = ""
    input_verilog = "{}/chipcompiler/thirdparty/ecc-tools/scripts/design/sky130_gcd/result/verilog/gcd.v".format(root)
    
    ecc_serv = ecc_service()
    
    parameters=get_parameters("sky130", "gcd")
    
    ecc_req = ECCRequest(
        cmd = "create_workspace",
        data = {
            "directory" : workspace_dir,
            "pdk" : "sky130",
            "parameters" : parameters.data,
            "origin_def" : input_def,
            "origin_verilog" : input_verilog,
            "rtl_list" : ""
        }
    )
    ecc_response = ecc_serv.create_workspace(ecc_req)
    
    ecc_req = ECCRequest(
        cmd = "load_workspace",
        data = {
            "directory" : workspace_dir
        }
    )
    ecc_response = ecc_serv.load_workspace(ecc_req)
    print(ecc_response)
    
    # ecc_req = ECCRequest(
    #     cmd = "delete_workspace",
    #     data = {
    #         "directory" : workspace_dir
    #     }
    # )
    # ecc_response = ecc_serv.delete_workspace(ecc_req)
    
    # ecc_req = ECCRequest(
    #     cmd = "rtl2gds",
    #     data = {
    #         "rerun" : True
    #     }
    # )
    # ecc_response = ecc_serv.rtl2gds(ecc_req)
    
    
    # test step    
    from chipcompiler.rtl2gds import build_rtl2gds_flow
    steps = build_rtl2gds_flow()
    for step, tool, state in steps:
        ecc_req = ECCRequest(
            cmd = "run_step",
            data = {
                "step" : step.value
            }
        )
        ecc_response = ecc_serv.run_step(ecc_req)
        print(ecc_response)
    
    print(1)
  

    
if __name__ == "__main__":
    test_sky130_gcd()

    exit(0)
