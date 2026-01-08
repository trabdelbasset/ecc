#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import os

current_dir = os.path.split(os.path.abspath(__file__))[0]
root = current_dir.rsplit('/', 1)[0]
sys.path.append(root)

from chipcompiler.data import Parameters

def get_parameters(pdk_name : str, design : str = "", path : str = "") -> Parameters:
    """
    Return the Parameters instance based on the given pdk name.
    """
    path = path if path != "" else f"{current_dir}/{pdk_name.lower()}_parameter.json"
    if pdk_name.lower() == "sky130":
        return parameter_sky130(design, path)
    elif pdk_name.lower() == "ics55":
        return parameter_ics55(design, path)
    else:
        return Parameters()

def parameter_ics55(design : str, path : str) -> Parameters:
    parameters = Parameters()
    
    from chipcompiler.utility import json_read
    parameters.path = path
    parameters.data = json_read(path)
    
    match design.lower():
        case "gcd":
            parameters.data["Design"] = "gcd"
            parameters.data["Top module"] = "gcd"
            parameters.data["Clock"] = "clk"
            parameters.data["Frequency max [MHz]"] = 100
        case "s713":
            parameters.data["Design"] = "s713"
            parameters.data["Top module"] = "s713"
            parameters.data["Clock"] = "CK"
            parameters.data["Frequency max [MHz]"] = 100

    return parameters

def parameter_sky130(design : str, path : str) -> Parameters:
    parameters = Parameters()
    
    from chipcompiler.utility import json_read
    parameters.path = path
    parameters.data = json_read(path)
    
    match design.lower():
        case "gcd":
            parameters.data["Design"] = "gcd"
            parameters.data["Top module"] = "gcd"
            parameters.data["Clock"] = "clk"
            parameters.data["Frequency max [MHz]"] = 100
        
    return parameters