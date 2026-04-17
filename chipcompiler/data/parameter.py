#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import json
import os
from copy import deepcopy
from dataclasses import dataclass, field

from chipcompiler.data.pdk import (
    ECC_PDK_CONFIG_FILENAME,
    _resolve_pdk_root,
    _resolve_env_vars_for_pdk,
)

ICS55_PARAMETERS_TEMPLATE = {
    "PDK":"ICS55",
    "Design":"",
    "Top module":"",
    "Die" : {
        "Size": [],
        "Area": 0
    },
    "Core" : {
        "Size": [],
        "Area" : 0,
        "Bounding box": "",
        "Utilitization": 0.4,
        "Margin" : [2, 2],
        "Aspect ratio" : 1
    },
    "Max fanout" : 20,
    "Target density" : 0.3,
    "Target overflow" : 0.1,
    "Global right padding": 0,
    "Cell padding x": 600,
    "Routability opt flag": 1,
    "Clock" : "",
    "Frequency max [MHz]" : 100,
    "Bottom layer" : "MET2",
    "Top layer" : "MET5",
    "Floorplan" : {
        "Tap distance" : 58,
        "Auto place pin" : {
          "layer" : "MET3",
          "width" : 300,
          "height" : 600,
          "sides" : []  
        },
        "Tracks" :[
            {
                "layer" : "MET1",
                "x start" : 0,
                "x step" : 200,
                "y start" : 0,
                "y step" : 200
            },
            {
                "layer" : "MET2",
                "x start" : 0,
                "x step" : 200,
                "y start" : 0,
                "y step" : 200
            },
            {
                "layer" : "MET3",
                "x start" : 0,
                "x step" : 200,
                "y start" : 0,
                "y step" : 200
            },
            {
                "layer" : "MET4",
                "x start" : 0,
                "x step" : 200,
                "y start" : 0,
                "y step" : 200
            },
            {
                "layer" : "MET5",
                "x start" : 0,
                "x step" : 200,
                "y start" : 0,
                "y step" : 200
            },
            {
                "layer" : "T4M2",
                "x start" : 0,
                "x step" : 800,
                "y start" : 0,
                "y step" : 800
            },
            {
                "layer" : "RDL",
                "x start" : 0,
                "x step" : 5000,
                "y start" : 0,
                "y step" : 5000
            }
        ]
    },
    "PDN" : {
        "IO" : [
            {
                "net name" : "VDD",
                "direction" : "INOUT",
                "is power" : True
            },
            {
                "net name" : "VDDIO",
                "direction" : "INOUT",
                "is power" : True
            },
            {
                "net name" : "VSS",
                "direction" : "INOUT",
                "is power" : False
            },
            {
                "net name" : "VSSIO",
                "direction" : "INOUT",
                "is power" : False
            }
        ],
        "Global connect" : [
            {
                "net name" : "VDD",
                "instance pin name" : "VDD",
                "is power" : True
            },
            {
                "net name" : "VDD",
                "instance pin name" : "VDD1",
                "is power" : True
            },
            {
                "net name" : "VDD",
                "instance pin name" : "VNW",
                "is power" : True
            },
            {
                "net name" : "VDDIO",
                "instance pin name" : "VDDIO",
                "is power" : True
            },
            {
                "net name" : "VSS",
                "instance pin name" : "VSS",
                "is power" : False
            },
            {
                "net name" : "VSS",
                "instance pin name" : "VSS1",
                "is power" : False
            },
            {
                "net name" : "VSS",
                "instance pin name" : "VPW",
                "is power" : False
            },
            {
                "net name" : "VSSIO",
                "instance pin name" : "VSSIO",
                "is power" : False
            }
        ],
        "Grid" : {
            "layer" : "MET1",
            "power net" : "VDD",
            "power ground" : "VSS",
            "width" : 0.16,
            "offset" : 0
        },
        "Stripe" : [
            {
                "layer" : "MET4",
                "power net" : "VDD",
                "ground net" : "VSS",
                "width" : 1,
                "pitch" : 16,
                "offset" : 0.5                        
            },
            {
                "layer" : "MET5",
                "power net" : "VDD",
                "ground net" : "VSS",
                "width" : 1,
                "pitch" : 16,
                "offset" : 0.5                        
            }
        ],
        "Connect layers" : [
            {
                "layers" : [
                    "MET1",
                    "MET5"
                ]
            },
            {
                "layers" : [
                    "MET4",
                    "MET5"
                ]
            }
        ]
    } 
}

ICS55_DESIGN_PARAMETERS = {
    "gcd": {
        "Design": "gcd",
        "Top module": "gcd",
        "Clock": "clk",
        "Frequency max [MHz]": 100,
    }
}

@dataclass
class Parameters:
    """
    Dataclass for design parameters
    """
    path : str = "" # parameters file path
    data : dict = field(default_factory=dict) # parameters data

def load_parameter(path : str) -> Parameters:
    from chipcompiler.utility import json_read
    parameter = Parameters()
    parameter.path = path
    parameter.data = json_read(path)
    return parameter
    
def save_parameter(parameter : Parameters) -> bool:
    from chipcompiler.utility import json_write
    return json_write(file_path=parameter.path,
                      data=parameter.data)

def load_parameters_from_json(pdk_name: str) -> dict:
    """
    Load the parameters template from ecc_pdk.json for an external PDK.
    Returns the "parameters" section as a dict, or empty dict if not found.
    """
    env_vars = _resolve_env_vars_for_pdk(pdk_name)
    pdk_root = _resolve_pdk_root("", env_vars)
    if not pdk_root:
        return {}
    config_path = os.path.join(pdk_root, ECC_PDK_CONFIG_FILENAME)
    if not os.path.isfile(config_path):
        return {}
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config.get("parameters", {})
    except (json.JSONDecodeError, OSError):
        return {}

def get_parameters(pdk_name: str = "", path: str = "") -> Parameters:
    if os.path.isfile(path):
        return load_parameter(path)

    parameters = Parameters()
    parameters.path = path

    pdk_lower = pdk_name.lower() if pdk_name else ""
    if pdk_lower == "ics55":
        parameters.data = deepcopy(ICS55_PARAMETERS_TEMPLATE)
    elif pdk_lower:
        template = load_parameters_from_json(pdk_lower)
        if template:
            parameters.data = deepcopy(template)

    return parameters

def get_design_parameters(pdk_name : str, design : str = "", path : str = "") -> Parameters:
    """
    Return parameters resolved by PDK and optional design name.
    """
    parameters = get_parameters(pdk_name, path)
    if not design or pdk_name.lower() != "ics55":
        return parameters

    design_info = ICS55_DESIGN_PARAMETERS.get(design.lower())
    if design_info is None:
        return parameters

    parameters.data.update(design_info)
    return parameters

def update_parameters(parameters_src : dict, parameters_target : dict) -> dict:
    """
    Update parameters_target with data from parameters_src.
    If a value is a list, it will be replaced entirely.
    If a value is a dict, it will be updated recursively.
    Otherwise, the value will be replaced.
    """
    for key, value in parameters_src.items():
        if key in parameters_target:
            if isinstance(value, list):
                # If it's a list, replace entirely
                parameters_target[key] = value
            elif isinstance(value, dict) and isinstance(parameters_target[key], dict):
                # If it's a dict, update recursively
                update_parameters(value, parameters_target[key])
            else:
                # For other types, replace
                parameters_target[key] = value
        else:
            # If key doesn't exist, add it
            parameters_target[key] = value

    return parameters_target
