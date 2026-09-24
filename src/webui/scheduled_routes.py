"""Scheduled-routes Web UI routes: transfer partners for award programs."""
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Request

from ..scheduled_runner import run_schedule
from ..transfer_partners import list_partners


class RunRequest(BaseModel):
    program: str | None = None

router = APIRouter(prefix="/api/scheduled")

TEMPLATES = []


def init(templates):
    global TEMPLATES
    TEMPLATES = templates


@router.get("/templates")
def scheduled_templates():
    return {"templates": TEMPLATES}


@router.get("/page/{name}")
def scheduled_page(request: Request, name: str):
    try:
        return TEMPLATES.TemplateResponse(name, {"request": request})
    except Exception:
        raise HTTPException(status_code=404, detail={"error": "template not found", "name": name})


@router.get("/partners")
def scheduled_partners():
    return {"partners": list_partners()}


@router.get("/partners/{code}")
def scheduled_partner(code: str):
    for partner in list_partners():
        if partner["code"].lower() == code.lower():
            return dict(partner)
    raise HTTPException(status_code=404, detail={"error": "partner not found", "code": code})


@router.post("/run")
def scheduled_run(body: RunRequest):
    if not body.program:
        raise HTTPException(status_code=422, detail={"error": "program is required", "code": "invalid_program"})
    return run_schedule(program=body.program)
