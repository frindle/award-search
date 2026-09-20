"""Scheduled-routes Web UI routes: transfer partners for award programs."""
from fastapi import APIRouter, HTTPException

from ..transfer_partners import list_partners

router = APIRouter(prefix="/api/scheduled")


@router.get("/partners")
def scheduled_partners():
    return {"partners": list_partners()}


@router.get("/partners/{code}")
def scheduled_partner(code: str):
    for partner in list_partners():
        if partner["code"].lower() == code.lower():
            return dict(partner)
    raise HTTPException(status_code=404, detail={"error": "partner not found", "code": code})
