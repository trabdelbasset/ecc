#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from chipcompiler.data import Workspace, WorkspaceStep

class EngineDB:
    """
    use iEDA-idb as the database engine
    """
    from chipcompiler.tools.iEDA import IEDAEngine
    def __init__(self, engine : IEDAEngine= None):
        self.engine = engine

    def create_db_engine(self,
                         workspace: Workspace,
                         step: WorkspaceStep) -> bool:
        # check eda tool exist
        from chipcompiler.tools import load_eda_module
        eda_module = load_eda_module("iEDA")
        if eda_module is None:
            return False
        
        self.engine = eda_module.create_db_engine(workspace, step)
        return True