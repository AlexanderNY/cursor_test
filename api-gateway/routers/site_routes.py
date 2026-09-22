"""DEPRECATED: 9to18 site API moved to nine-to-eighteen/api (site-api).

This module is no longer mounted in the gateway. Kept for reference / rollback.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/site", tags=["Site9to18-deprecated"])
