"""Adversarial fixture for: aw-app-wiring-s5-app-include-router-sched

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
import sys
import types

# `from . import scheduled_routes` (landed by slice s3) requires a sibling module
# src/webui/scheduled_routes.py that does not exist yet in this worktree. The
# fixture is the only thing allowed to touch anything besides app.py, so register
# a minimal stub in sys.modules BEFORE importing the target: `from . import X`
# resolves through sys.modules and finds it there. This exercises exactly what
# the slice wires -- the router object handed to include_router -- without
# inventing scheduled-route behaviour that belongs to later slices.
try:
    from fastapi import APIRouter as _APIRouter
except ImportError:  # pragma: no cover - fastapi is a hard dep of the target
    raise SystemExit("fastapi is required to run this fixture")

# The stub router carries two real routes with known bodies. If app.py calls
# include_router(scheduled_routes.router), these paths are mounted and answer
# 200 with exactly that body; if it does not, the same requests fall through to
# FastAPI's no-route branch -> 404 {"detail": "Not Found"}. That is what makes
# this fixture discriminate a correct wiring from an absent one.
_stub_router = _APIRouter()


@_stub_router.get("/scheduled")
async def _stub_scheduled_list():
    return {"ok": True, "schedules": []}


@_stub_router.post("/scheduled/{schedule_id}/run")
async def _stub_scheduled_run(schedule_id: str):
    return {"ok": True, "ran": schedule_id}


_stub = types.ModuleType("src.webui.scheduled_routes")
_stub.router = _stub_router
sys.modules["src.webui.scheduled_routes"] = _stub

# app.py uses relative imports (`from ..browser.manager import ...`), so it must
# be loaded as part of its real package, not via spec_from_file_location (which
# has no parent package and dies on the first `..`). A normal package import
# registers src.webui.app in sys.modules itself -- which is what keeps dataclass
# string-annotation resolution working on Python 3.14.
sys.path.insert(0, ".")
import src.webui.app as target  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

_client = TestClient(target.app)


def _get_scheduled():
    r = _client.get("/scheduled")
    return (r.status_code, r.json())


def _post_run():
    r = _client.post("/scheduled/sched_123/run", json={})
    return (r.status_code, r.json())


def _home_regression():
    # Regression half: including the router must not disturb existing routes.
    r = _client.get("/")
    return (r.status_code, "Award Search" in r.text)



CASES = [
    # Discriminator: with include_router(scheduled_routes.router) present, the
    # stub router's GET /scheduled is mounted -> 200 with its exact body.
    # Without it, the same request hits FastAPI's no-route branch ->
    # 404 {"detail": "Not Found"}. Status AND body both pin the wiring.
    ("GET /scheduled serves the router's route (mounted)", _get_scheduled,
     (200, {"ok": True, "schedules": []})),
    # Second discriminator on a different method/path: a plausible wrong fix
    # that mounts only some routes (or a differently-named router) fails here.
    ("POST /scheduled/{id}/run serves the router's route (mounted)", _post_run,
     (200, {"ok": True, "ran": "sched_123"})),
    # Regression half: the pre-existing home route must keep working after the
    # router is included.
    ("GET / still serves the Award Search page", _home_regression,
     (200, True)),
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
