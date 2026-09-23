"""Adversarial fixture for: aw-sched-runner-s26-sleeps-poll-minutes-or-d

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
import importlib.util
import sys
import types

spec = importlib.util.spec_from_file_location("target", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["target"] = target

# The target uses package-relative imports (from .alert_filters import ...).
# Loaded standalone it has no parent package, so give it a stub "src" package
# whose sibling modules expose exactly the names the target binds. This keeps
# the fixture hermetic -- none of the heavy real siblings get imported.
def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m


_stub("src", __path__=[])
_stub("src.alert_filters", passes_filters=lambda *a, **k: True)
_stub("src.deeplinks", seats_aero_url=lambda *a, **k: "")
_stub("src.pushover", send_award_notification=lambda *a, **k: None)


class _StubClient:
    pass


_stub("src.seats_aero", SeatsAeroClient=_StubClient)
_stub(
    "src.scheduled_searches",
    effective_programs=lambda *a, **k: [],
    is_due=lambda *a, **k: False,
    load_schedules=lambda *a, **k: {},
    query_legs=lambda *a, **k: [],
    upsert_schedule=lambda *a, **k: None,
)

target.__package__ = "src"
spec.loader.exec_module(target)


class _StopLoop(Exception):
    """Sentinel raised by the fake sleep to end a tick loop after N ticks."""


def run_ticks(poll_minutes, max_calls=2):
    """Run schedule_scheduler with asyncio.sleep faked; return the list of
    seconds it was asked to sleep for. The fake raises _StopLoop once
    max_calls sleeps have been recorded, so an infinite loop is bounded and a
    one-shot (non-looping) implementation returns fewer calls than expected."""
    calls = []

    async def fake_sleep(seconds):
        calls.append(seconds)
        if len(calls) >= max_calls:
            raise _StopLoop()

    orig = target.asyncio.sleep
    target.asyncio.sleep = fake_sleep
    try:
        asyncio.run(target.schedule_scheduler(poll_minutes))
    except _StopLoop:
        pass
    finally:
        target.asyncio.sleep = orig
    return calls


CASES = [
    ("explicit poll_minutes=2 sleeps 120s on every tick (loop, not one-shot)",
     lambda: run_ticks(2, 3), [120, 120, 120]),
    ("poll_minutes=None falls back to DEFAULT_POLL_MINUTES*60 = 300s",
     lambda: run_ticks(None, 2), [300, 300]),
    ("poll_minutes=0 is falsy -- `or` picks the default (300s, not 0)",
     lambda: run_ticks(0, 1), [300]),
    ("DEFAULT_POLL_MINUTES is 5 minutes",
     lambda: target.DEFAULT_POLL_MINUTES, 5),
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
