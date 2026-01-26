#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from pydantic import BaseModel
from enum import Enum
from typing import List

class CMDEnum(Enum):
    create_workspace = "create_workspace"
    load_workspace = "load_workspace"
    delete_workspace = "delete_workspace"
    rtl2gds = "rtl2gds"
    run_step = "run_step"

class ResponseEnum(Enum):
    success = "success"
    failed = "failed"
    error = "error"

DATA_TEMPLATE = {
    "create_workspace" : {
        "requeset" : {
            "directory" : "",
            "pdk" : "",
            "parameters" : {},
            "origin_def" : "",
            "origin_verilog" : "",
            "rtl_list" : ""
        },
        "response" : {
            "directory" : ""
        }
    },
    
    "load_workspace" : {
        "requeset" : {
            "directory" : ""
        },
        "response" : {
            "directory" : ""
        }
    },
    
    "delete_workspace" : {
        "requeset" : {
            "directory" : ""
        },
        "response" : {
            "directory" : ""
        }
    },
    
    "rtl2gds" : {
        "requeset" : {
            "rerun" : False
        },
        "response" : {
            "rerun" : False
        }
    },
    
    "run_step" : {
        "requeset" : {
            "step" : ""
        },
        "response" : {
            "step" : "",
            "state" : "Unstart"
        }
    },
}

class ECCRequest(BaseModel):
    """
    """
    cmd : str
    data : dict
    
class ECCResponse(BaseModel):
    """
    """
    cmd : str
    response : str
    data : dict
    message : list