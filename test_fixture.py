"""Adversarial fixture for: aw-sched-runner-s25-sleeps-20s-then-forever

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
import importlib.util


def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


# The target uses relative imports (from .scheduled_searches import ...).
# scheduled_searches does not exist yet in this slice chain, and the other
# sibling modules pull third-party deps / credentials at import time. Stub every
# relative dependency so the module under test loads in isolation; the cases
# below patch target.load_schedules / target.is_due / target.run_schedule with
# their own spies anyway.
_stub("src")
_stub("src.alert_filters", passes_filters=lambda c, f: True)
_stub("src.deeplinks", seats_aero_url=lambda *a, **k: "https://seats.aero/")
_stub("src.pushover", send_award_notification=lambda *a, **k: None)
_stub("src.seats_aero", SeatsAeroClient=object)
_stub(
    "src.scheduled_searches",
    effective_programs=lambda *a, **k: [],
    is_due=lambda s: False,
    load_schedules=lambda: [],
    query_legs=lambda *a, **k: [],
    upsert_schedule=lambda s: None,
)

spec = importlib.util.spec_from_file_location("src.scheduled_runner", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["target"] = target
sys.modules["src.scheduled_runner"] = target
spec.loader.exec_module(target)


class _Stop(Exception):
    """Sentinel raised by the fake clock once enough ticks have been observed."""


def _drive(poll_minutes=None, max_sleeps=2, schedules="__unset__", due_ids=frozenset(),
           run_side_effect=None):
    """Run schedule_scheduler under a fake clock with spied schedule helpers.

    Returns (sleeps, to_thread_args) where `sleeps` is the ordered list of
    seconds passed to asyncio.sleep and `to_thread_args` is the list of sched
    objects routed through asyncio.to_thread by the loop body."""
    sleeps = []
    calls = []
    real_sleep = target.asyncio.sleep
    real_to_thread = target.asyncio.to_thread

    async def fake_sleep(secs):
        sleeps.append(secs)
        if len(sleeps) >= max_sleeps:
            raise _Stop

    def spy_to_thread(fn, *a):
        calls.append(a[0] if a else None)
        return real_to_thread(fn, *a)

    orig = {k: getattr(target, k) for k in ("load_schedules", "is_due", "run_schedule")}
    target.load_schedules = (lambda: None if schedules is None else list(schedules)) \
        if schedules != "__unset__" else orig["load_schedules"]
    target.is_due = (lambda s: (s or {}).get("id") in due_ids) if due_ids is not None else orig["is_due"]

    def fake_run(sched=None, *a, **k):
        if run_side_effect is not None:
            raise run_side_effect
        return []

    target.run_schedule = fake_run
    target.asyncio.sleep = fake_sleep
    target.asyncio.to_thread = spy_to_thread
    try:
        asyncio.run(target.schedule_scheduler(poll_minutes))
    except _Stop:
        pass
    finally:
        for k, v in orig.items():
            setattr(target, k, v)
        target.asyncio.sleep = real_sleep
        target.asyncio.to_thread = real_to_thread
    return sleeps, calls



CASES = [
    (
        "first action is a 20s sleep before any schedule work",
        lambda: (lambda s, c: (s[0], len(c)))(*_drive(max_sleeps=1)),
        (20, 0),
    ),
    (
        "due schedules run via asyncio.to_thread(run_schedule, s); non-due are skipped; loop continues to the poll sleep",
        lambda: (lambda s, c: (c, s[-1]))(
            *_drive(max_sleeps=2, schedules=[{"id": "due-1"}, {"id": "skip-2"}], due_ids=frozenset({"due-1"}))
        ),
        ([{"id": "due-1"}], 300),
    ),
    (
        "load_schedules() returning None must not raise; loop still reaches the poll sleep",
        lambda: (lambda s, c: ("survived" if len(s) >= 2 else "died", s[-1]))(
            *_drive(max_sleeps=2, schedules=None)
        ),
        ("survived", 300),
    ),
    (
        "a run_schedule exception is contained per-schedule; the loop keeps running",
        lambda: (lambda s, c: ("survived" if len(s) >= 2 else "died"))(
            *_drive(max_sleeps=2, schedules=[{"id": "boom"}], due_ids=frozenset({"boom"}),
                   run_side_effect=RuntimeError("pushover down"))
        ),
        "survived",
    ),
    (
        "poll interval honours poll_minutes: 1 minute -> 60s between ticks",
        lambda: (lambda s, c: s[-1])(*_drive(poll_minutes=1, max_sleeps=2)),
        60,
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
