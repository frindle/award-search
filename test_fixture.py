"""Adversarial fixture for: aw-app-wiring-v2

>>> THE ONE THING THE GENERATOR CANNOT WRITE FOR YOU <<<

CASES is empty and the verify FAILS until you fill it in. That is deliberate.
A generator can emit a verify that DISCRIMINATES (fails at baseline, passes on
a fix). It cannot decide whether the verify is RELEVANT -- whether it tests the
property the task actually asked for. A benign case passes broken work.

Pick inputs that separate "did the job" from "made the test go green":
  * the exact boundary the defect is about, and one on each side of it
  * the degenerate inputs (missing key, None, empty, wrong type) that must NOT
    raise
  * at least one case that a plausible WRONG fix would fail
  * the regression half: things that already work and must keep working

Each case: (description, callable_returning_actual, expected)
"""
import asyncio
import sys
import types
from pathlib import Path

# --- load the real app through its package path -----------------------------
# app.py uses relative imports (`from ..alerts import ...`), so it cannot be
# loaded as a bare top-level module. Load it as `src.webui.app`.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# The scheduled-search routes module lands from a sibling slice and is not in
# this worktree yet. Stub it BEFORE importing app.py so the import resolves;
# the stub also records what app.py hands to it (the Jinja2Templates instance)
# and whether the background loop coroutine was actually started.
_stub = types.ModuleType("src.webui.scheduled_routes")

_loop_started = {"v": False}


async def _stub_scheduled_search_loop():
    _loop_started["v"] = True
    await asyncio.sleep(3600)  # stay alive like a real background loop


_templates_seen = []


def _stub_create_router(tpl):
    from fastapi import APIRouter

    _templates_seen.append(tpl)
    r = APIRouter(prefix="/api/scheduled")

    @r.get("/ping")
    def ping():  # pragma: no cover - stub endpoint, proves the mount
        return {"ok": True}

    return r


_stub.create_router = _stub_create_router
_stub.scheduled_search_loop = _stub_scheduled_search_loop
sys.modules["src.webui.scheduled_routes"] = _stub

from src.webui import app as target  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def _routes():
    return [getattr(r, "path", None) for r in target.app.routes]


# --- cases ------------------------------------------------------------------

CASES = [
    (
        "scheduled_routes APIRouter is mounted on the app (/api/scheduled/ping route present)",
        lambda: any(p == "/api/scheduled/ping" for p in _routes()),
        True,
    ),
    (
        "app hands its own Jinja2Templates instance to create_router",
        lambda: bool(_templates_seen) and _templates_seen[0] is target.templates,
        True,
    ),
    (
        "scheduled_search_loop background task starts on app startup",
        lambda: (TestClient(target.app).__enter__(), _loop_started["v"])[1],
        True,
    ),
    (
        "regression: existing /api/alerts/{id}/results still returns 404 for unknown id",
        lambda: TestClient(target.app).get("/api/alerts/does-not-exist/results").status_code,
        404,
    ),
]


def main():
    if len(CASES) < 3:
        print("  SCAFFOLD_INCOMPLETE: {} adversarial case(s) authored, need >= 3."
              .format(len(CASES)))
        print("  A generated scaffold is not a verify. Author the cases in "
              "test_fixture.py.")
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
