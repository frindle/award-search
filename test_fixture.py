"""Adversarial fixture for: aw-sched-routes-s15-post-scheduled-sched-id

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
import importlib.util
import sys
import threading
import types

# The target does relative imports (`from ..scheduled_runner import ...`) whose
# modules are not part of this slice. Register minimal stand-ins BEFORE exec so
# the module loads; cases then patch `target.run_schedule` directly (the route
# resolves that name from module globals at call time).
_runner = types.ModuleType("src.scheduled_runner")


def _unpatched_run_schedule(*a, **k):
    raise AssertionError("fixture forgot to patch target.run_schedule")


_runner.run_schedule = _unpatched_run_schedule
_partners = types.ModuleType("src.transfer_partners")
_partners.list_partners = lambda: []
sys.modules.setdefault("src.scheduled_runner", _runner)
sys.modules.setdefault("src.transfer_partners", _partners)

spec = importlib.util.spec_from_file_location(
    "src.webui.scheduled_routes", 'src/webui/scheduled_routes.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["src.webui.scheduled_routes"] = target
spec.loader.exec_module(target)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()
app.include_router(target.router)
client = TestClient(app)

MAIN_THREAD_ID = threading.get_ident()


def _post_run(sched_id):
    r = client.post("/api/scheduled/{}/run".format(sched_id))
    return (r.status_code, r.json())


CASES = [
    ("unknown sched_id -> 404 with the schedule-not-found error body",
     lambda: _post_run("no-such-id"),
     (404, {"detail": {"error": "schedule not found", "sched_id": "no-such-id"}})),

    ("run passes the STORED schedule to run_schedule and returns its result verbatim",
     lambda: (lambda calls, sched: (
         target.SCHEDULES.__setitem__("s1", dict(sched)),
         setattr(target, "run_schedule", lambda s: calls.append(s) or {"ran": True}),
         _post_run("s1") + (calls,))[-1])([], {"id": "s1", "name": "one", "enabled": True}),
     (200, {"ran": True}, [{"id": "s1", "name": "one", "enabled": True}])),

    ("run_schedule executes OFF the request thread (threadpool), not inline",
     lambda: (lambda rec: (
         target.SCHEDULES.__setitem__("s2", {"id": "s2"}),
         setattr(target, "run_schedule", lambda s: rec.update(
             ident=threading.get_ident(), result={"ok": True})),
         _post_run("s2")[0] == 200 and rec["ident"] != MAIN_THREAD_ID
         and rec["result"] == {"ok": True})[-1])({}),
     True),

    ("run does not mutate the stored schedule dict it hands to run_schedule",
     lambda: (lambda sched: (
         target.SCHEDULES.__setitem__("s3", sched),
         setattr(target, "run_schedule", lambda s: {"ran": True}),
         _post_run("s3")[0] == 200 and target.SCHEDULES["s3"] == sched)[-1])({
             "id": "s3", "name": "three", "enabled": False, "programs": ["PRG"]}),
     True),

    ("run with an empty-body POST (no JSON) still resolves by path id -> 200",
     lambda: (lambda calls: (
         target.SCHEDULES.__setitem__("s4", {"id": "s4"}),
         setattr(target, "run_schedule", lambda s: calls.append(s["id"]) or {"ok": True}),
         client.post("/api/scheduled/s4/run").json() == {"ok": True} and calls == ["s4"])[-1])([]),
     True),
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
