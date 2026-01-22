#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from fastapi import APIRouter, HTTPException

from ..schemas import (
    ECCRequest,
    ECCResponse
)
from ..services import ecc_service

ecc_serv = ecc_service()

router = APIRouter(prefix="/api/workspace", tags=["workspace"])

@router.post("/create_workspace", response_model=ECCResponse)
async def create_workspace(request: ECCRequest):
    """
    Create a new ECC project.
    """
    return ecc_serv.create_workspace(request)

@router.post("/load_workspace", response_model=ECCResponse)
async def load_workspace(request: ECCRequest):
    """
    Open an existing ECC project.
    """
    return ecc_serv.load_workspace(request)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}
