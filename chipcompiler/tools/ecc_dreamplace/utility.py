#!/usr/bin/env python
# -*- encoding: utf-8 -*-

def is_eda_exist() -> bool:
    # check ecc exist
    from chipcompiler.tools.ecc.utility import is_eda_exist as is_ecc_exist
    if not is_ecc_exist():
        return False
    
    # check ecc-dreamplace exist 
    try:
        from dreamplace.Params import Params
        from dreamplace.Placer import PlacementEngine
        return True
    except Exception:
        return False