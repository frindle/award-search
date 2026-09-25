#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s11-preserves-created-at-las

Adds POST /api/scheduled/{sched_id} (scheduled_edit_save) to
src/webui/scheduled_routes.py. The edit merges the submitted fields into the
existing record but PRESERVES created_at/last_checked/last_results/
notified_keys from the existing record -- a naive "replace with body" impl
would wipe them, and the fixture asserts they survive.

The gate applies this, runs the verify, and reverts it.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

OLD = r'''def parse_csv(value: Optional[str]) -> List[str]:'''

NEW = r'''class EditRequest(BaseModel):
    name: str | None = None
    origins: List[str] | None = None
    destinations: List[str] | None = None
    date_ranges: List[Dict] | None = None
    cabins: List[str] | None = None
    programs: List[str] | None = None
    transfer_partners: List[str] | None = None
    filters: Dict | None = None
    interval_hours: int | float | None = None
    notify_pushover: bool | None = None
    enabled: bool | None = None


@router.post("/{sched_id}")
def scheduled_edit_save(sched_id: str, body: EditRequest):
    existing = SCHEDULES.get(sched_id)
    if existing is None:
        raise HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})
    updated = dict(existing)
    for key in ("name", "origins", "destinations", "date_ranges", "cabins",
                "programs", "transfer_partners", "filters", "interval_hours",
                "notify_pushover", "enabled"):
        value = getattr(body, key)
        if value is not None:
            updated[key] = value
    # PRESERVES created_at/last_checked/last_results/notified_keys from the existing record on an edit.
    updated["created_at"] = existing.get("created_at")
    updated["last_checked"] = existing.get("last_checked")
    updated["last_results"] = existing.get("last_results")
    updated["notified_keys"] = list(existing.get("notified_keys") or [])
    SCHEDULES[sched_id] = updated
    return {"schedule": normalize_schedule(updated)}


def parse_csv(value: Optional[str]) -> List[str]:'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
