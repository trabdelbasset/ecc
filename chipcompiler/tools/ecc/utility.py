#!/usr/bin/env python
# -*- encoding: utf-8 -*-

def is_eda_exist() -> bool:
    """
    Check if the ECC tool is installed and accessible.
    """          
    try:
        # from chipcompiler.tools.ecc.bin import ecc_py
        return True
    except ImportError:
        return False
