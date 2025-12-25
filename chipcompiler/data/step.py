#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from enum import Enum
from dataclasses import dataclass, field

class StepEnum(Enum):
    """RTL2GDS flow step names"""
    RTL2GDS = "RTL2GDS"
    INIT = "Init"
    SOC = "SOC"
    FUNC_SIM = "Functional simulation"
    SYNTHESIS = "Synthesis"
    FLOORPLAN = "Floorplan"
    NETLIST_OPT = "Netlist optimization"
    PLACEMENT = "Placement"
    CTS = "CTS"
    TIMING_OPT = "Timing optimization"
    LEGALIZATION = "Legalization"
    ROUTING = "Routing"
    FILLER = "Filler"
    GDS = "GDS"    
    SIGNOFF = "Signoff"
    STA = "STA"
    DRC = "DRC"
    RCX = "RCX"
    ABSTRACT_LEF = "Abstract lef"
    MERGE = "GDS merge"

class StateEnum(Enum):
    """flow running state"""
    Invalid = "Invalid" # iEDA or config invalid
    Unstart = "Unstart" # step unstart
    Success = "Success" # step run success
    Ongoing = "Ongoing" # step is running
    Pending = "Pending" # step is pending
    Imcomplete = "Incomplete" # step is failed
    Ignored = "Ignored" # step result do not affect flow step
    

###########################################################################
# step definition for chip design flow
# step_definition =
# {
#     "name" : "", # step name
#     "tool" : "", # eda tool name
#     "state" : "", # step state
#     "runtime" : "", # step run time
#     "info" : {} # step additional infomation
# }
###########################################################################