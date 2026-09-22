"""Adversarial fixture for: aw-app-wiring-s6-sched-task-asyncio-creat

The target (src/webui/app.py) uses relative imports, so it must be loaded as a
package module (`src.webui.app`), not via spec_from_file_location. `scheduled_routes`
is authored by a sibling slice and may be absent in this worktree, so the fixture
shims it in sys.modules BEFORE import -- that is test scaffolding, not part of
the solution under test.

Cases assert the INTENT: lifespan() must create a task from
asyncio.create_task(schedule_scheduler()) while keeping the existing alert
scheduler task alive (regression half). A benign/unmodified app.py fails case 1
and case 3; an implementation that drops the alert task fails case 2.
"""
import asyncio
import inspect
import sys
import types

sys.path.insert(0, ".")

# Shim the sibling-slice module if it is not present in this worktree.
try:
    import src.webui.scheduled_routes  # noqa: F401
except ImportError:
    from fastapi import APIRouter
    shim = types.ModuleType("src.webui.scheduled_routes")
    shim.init = lambda *a, **k: None
    shim.router = APIRouter()
    sys.modules["src.webui.scheduled_routes"] = shim

import src.webui.app as target  # noqa: E402


def _lifespan_task_names():
    """Run lifespan startup under a spy on asyncio.create_task and return the
    coroutine names it was called with."""
    names = []
    real_create_task = asyncio.create_task

    def spy(coro, *a, **k):
        try:
            name = getattr(coro, "__name__", None)
            if name is None and coro.cr_frame is not None:
                name = coro.cr_frame.f_code.co_name
            names.append(name)
        except Exception:
            pass
        return real_create_task(coro, *a, **k)

    asyncio.create_task = spy
    loop = asyncio.new_event_loop()
    try:
        cm = target.lifespan(target.app)
        loop.run_until_complete(cm.__aenter__())
        for t in list(asyncio.all_tasks(loop)):
            t.cancel()
        loop.run_until_complete(cm.__aexit__(None, None, None))
    finally:
        asyncio.create_task = real_create_task
        loop.close()
    return names



CASES = [
    ("lifespan schedules the scheduler task via create_task",
     lambda: "schedule_scheduler" in _lifespan_task_names(), True),
    ("regression: existing alert scheduler task still scheduled",
     lambda: "alert_scheduler" in _lifespan_task_names(), True),
    ("schedule_scheduler is an async function (create_task-able)",
     lambda: inspect.iscoroutinefunction(target.schedule_scheduler), True),
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
