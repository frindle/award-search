"""Adversarial fixture for: aw-app-wiring-s7-imported-as-from-schedul

Integration fixture: drives the real FastAPI app through TestClient (status
codes AND response bodies) and inspects the wiring the slice is about -- that
`schedule_scheduler` in src/webui/app.py is the one imported from
src/scheduled_runner (not a local placeholder), and that lifespan() cancels
BOTH background tasks on shutdown.

A plausible-but-wrong implementation fails here:
  * keeping the local stub -> case 1 (module origin) and case 2 (placeholder
    text still in source) fail;
  * importing but not cancelling sched_task -> case 3 fails (only one cancel);
  * deleting the import without adding it -> app.py does not even parse/import.

The `src.webui.scheduled_routes` sibling module is a later slice and does not
exist yet, so we register a minimal stub in sys.modules before importing the
app -- exactly what the real deployment gets once that slice lands.
"""
import asyncio
import importlib.util
import pathlib
import re
import sys
import types

# --- make `src` importable from this worktree -------------------------------
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Stub the not-yet-landed sibling module app.py imports at module scope.
_stub = types.ModuleType("src.webui.scheduled_routes")
from fastapi import APIRouter  # noqa: E402
_stub.router = APIRouter()
_stub.init = lambda templates: None
sys.modules.setdefault("src.webui.scheduled_routes", _stub)

import src.webui.app as target  # noqa: E402
import src.scheduled_runner as runner  # noqa: E402


def _client():
    from fastapi.testclient import TestClient
    return TestClient(target.app)


# --- cases ------------------------------------------------------------------

# Model-drafted; NOT yet read by a human.
DRAFT_UNCONFIRMED = True

CASES = [
    (
        "schedule_scheduler in app.py IS the one from scheduled_runner",
        lambda: target.schedule_scheduler is runner.schedule_scheduler,
        True,
    ),
    (
        "placeholder stub text is gone from src/webui/app.py",
        lambda: "Placeholder for the scheduled-routes scheduler loop" not in pathlib.Path(
            ROOT / "src" / "webui" / "app.py").read_text(),
        True,
    ),
    (
        "lifespan shutdown cancels BOTH background tasks (alert + sched)",
        lambda: _shutdown_cancel_counts() == 2,
        True,
    ),
    (
        "GET / still serves the home page (status + body)",
        lambda: _home_ok(),
        True,
    ),
    (
        "unknown search id -> 404 with the right error shape",
        lambda: _notfound_ok(),
        True,
    ),
    (
        "POST /search with missing required fields -> 422, not a 500",
        lambda: _bad_search_ok(),
        True,
    ),
]


class _FakeTask(asyncio.Future):
    """Stands in for asyncio.Task; records whether cancel() was called.

    Subclasses Future so the event loop's bookkeeping (done callbacks etc.)
    works on it -- a plain object hangs `asyncio.run`'s shutdown."""

    def __init__(self, coro, loop=None):
        super().__init__(loop=loop)
        try:
            coro.close()  # don't leak the coroutine
        except Exception:
            pass
        self.cancelled = False

    def cancel(self):
        self.cancelled = True
        return True


def _shutdown_cancel_counts():
    """Run lifespan() to completion and count how many tasks it cancels.

    Patch `asyncio.create_task` at module scope (app.py calls the unqualified
    name, resolved through its own `asyncio` import) so both background tasks
    are recorded as fakes; then drive lifespan enter+exit on a manually-run
    event loop -- deliberately NOT asyncio.run(), whose Runner cancels every
    pending task at shutdown and would pollute (and hang on) the fake objects."""
    created = []
    real_create_task = target.asyncio.create_task

    def fake_create_task(coro, **kw):
        t = _FakeTask(coro)
        created.append(t)
        return t

    loop = asyncio.new_event_loop()
    try:
        async def _drive():
            async with target.lifespan(target.app):
                pass  # enter lifespan (tasks created), then exit it (shutdown runs)

        target.asyncio.create_task = fake_create_task
        loop.run_until_complete(_drive())
    finally:
        target.asyncio.create_task = real_create_task
        loop.close()

    return sum(1 for t in created if getattr(t, "cancelled", False))


def _home_ok():
    with _client() as c:
        r = c.get("/")
        return r.status_code == 200 and "Award Search" in r.text


def _notfound_ok():
    with _client() as c:
        r = c.get("/results/does_not_exist")
        return (r.status_code, r.json()) == (404, {"detail": "Search not found"})


def _bad_search_ok():
    with _client() as c:
        r = c.post("/search", data={})
        return r.status_code == 422


# --- runner -----------------------------------------------------------------

def main():
    if len(CASES) < 3:
        print("  SCAFFOLD_INCOMPLETE: {} adversarial case(s) authored, need >= 3."
              .format(len(CASES)))
        return 1
    fails = 0
    for desc, thunk, want in CASES:
        try:
            got = thunk()
        except Exception as e:
            print("  FAIL {} -- raised {}: {}".format(desc, type(e).__name__, e))
            fails += 1
            continue
        if got != want:
            print("  FAIL {} -- got {!r}, want {!r}".format(desc, got, want))
            fails += 1
    print("  {}/{} case(s) passed".format(len(CASES) - fails, len(CASES)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
