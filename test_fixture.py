"""Adversarial fixture for: aw-sched-routes-s3-from-scheduled-runner-im

INTEGRATION fixture: drives the real router through fastapi.testclient,
asserting status codes AND response bodies. The sibling modules
(src.transfer_partners, src.scheduled_runner) are stubbed in sys.modules
BEFORE the target is exec'd so relative imports resolve deterministically and
the fake run_schedule records every call -- a plausible-but-wrong impl that
hardcodes a response without calling run_schedule fails case 1.

Each case: (description, callable_returning_actual, expected)
"""
import importlib.util
import pathlib
import sys
import types


def _pkg(name):
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m
    return m


_pkg("src")
_pkg("src.webui")

CALLS = []


def fake_run_schedule(program):
    CALLS.append(program)
    return {"status": "scheduled", "program": program, "job_id": "job-123"}


_sr = types.ModuleType("src.scheduled_runner")
_sr.run_schedule = fake_run_schedule
sys.modules["src.scheduled_runner"] = _sr

_TP = types.ModuleType("src.transfer_partners")
_TP.list_partners = lambda: [
    {"code": "UA", "name": "United"},
    {"code": "DL", "name": "Delta"},
]
sys.modules["src.transfer_partners"] = _TP

spec = importlib.util.spec_from_file_location(
    "src.webui.scheduled_routes", pathlib.Path("src/webui/scheduled_routes.py"))
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC so the module is resolvable by name during exec.
sys.modules[spec.name] = target
spec.loader.exec_module(target)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()
app.include_router(target.router)
client = TestClient(app)


def _post_run(payload):
    r = client.post("/api/scheduled/run", json=payload)
    return (r.status_code, r.json())


CASES = [
    ("POST /run with a program calls run_schedule and returns its result verbatim",
     lambda: (_post_run({"program": "united"}), list(CALLS)),
     ((200, {"status": "scheduled", "program": "united", "job_id": "job-123"}), ["united"])),

    ("POST /run with missing program is a 422 with the spec error shape, not a 500",
     lambda: _post_run({}),
     (422, {"detail": {"error": "program is required", "code": "invalid_program"}})),

    ("POST /run with an empty-string program is the same 422 and does NOT call run_schedule",
     lambda: (_post_run({"program": ""}), list(CALLS)),
     ((422, {"detail": {"error": "program is required", "code": "invalid_program"}}), ["united"])),

    ("regression: GET /partners still returns the partner list",
     lambda: (lambda r: (r.status_code, r.json()))(client.get("/api/scheduled/partners")),
     (200, {"partners": [{"code": "UA", "name": "United"}, {"code": "DL", "name": "Delta"}]})),

    ("regression: GET /partners/{code} is case-insensitive and 404s unknown codes with the spec shape",
     lambda: ((lambda r: (r.status_code, r.json()))(client.get("/api/scheduled/partners/ua")),
              (lambda r: (r.status_code, r.json()))(client.get("/api/scheduled/partners/zz"))),
     ((200, {"code": "UA", "name": "United"}),
      (404, {"detail": {"error": "partner not found", "code": "zz"}}))),
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
