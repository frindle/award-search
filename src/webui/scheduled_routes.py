"""Scheduled-routes Web UI routes: airport groups and transfer partners."""
from fastapi import APIRouter, HTTPException

from ..airport_groups import list_groups, expand_codes

router = APIRouter(prefix="/api/scheduled")


@router.get("/groups")
def scheduled_groups():
    return {"groups": list_groups()}


@router.get("/codes/{codes}")
def scheduled_expand(codes: str):
    expanded = expand_codes([c for c in codes.split(",") if c.strip()])
    if not expanded:
        raise HTTPException(status_code=400, detail={"error": "no airport codes supplied"})
    return {"codes": expanded}


@router.get("/partners")
def scheduled_partners():
    return {"partners": []}


@router.get("/partners/{code}")
def scheduled_partner(code: str):
    raise HTTPException(status_code=404, detail={"error": "partner not found", "code": code})
