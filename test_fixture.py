"""Adversarial fixture for: aw-sched-runner-s8-module-constants-default

The target module uses relative imports (`from .alert_filters import ...`).
Loaded as a bare top-level module it has no parent package, so we pre-register
lightweight stand-ins for each imported name in sys.modules BEFORE exec. The
fixture only asserts on the three module constants -- the stubs just make the
module importable; they are not under test.

CASES: (description, callable_returning_actual, expected)
"""
import sys
import types
import importlib.util


def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m


class _Client:
    def search(self, *a, **k):
        return []

    def get_trip(self, availability_id):
        raise RuntimeError("no network in fixture")


_stub("src.alert_filters", passes_filters=lambda r, f: True)
_stub("src.deeplinks", seats_aero_url=lambda *a, **k: "")
_stub("src.pushover", send_award_notification=lambda *a, **k: None)
_stub("src.seats_aero", SeatsAeroClient=_Client)
_stub(
    "src.scheduled_searches",
    effective_programs=lambda *a, **k: [],
    is_due=lambda *a, **k: False,
    load_schedules=lambda *a, **k: {},
    query_legs=lambda *a, **k: [],
    upsert_schedule=lambda *a, **k: None,
)

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
# Give it a parent package name so its relative imports resolve against the
# stubs registered above.
target.__package__ = "src"
spec.loader.exec_module(target)


CASES = [
    # Value AND type: `15` (int) == 15.0 in Python, so a wrong impl that drops
    # the decimal must fail on the type half of this tuple.
    ("DEFAULT_POLL_MINUTES is exactly 15.0 (a float)",
     lambda: (target.DEFAULT_POLL_MINUTES, type(target.DEFAULT_POLL_MINUTES).__name__),
     (15.0, "float")),
    ("MAX_LEGS_PER_RUN is exactly 60 (an int)",
     lambda: (target.MAX_LEGS_PER_RUN, type(target.MAX_LEGS_PER_RUN).__name__),
     (60, "int")),
    ("NOTIFIED_KEYS_CAP is exactly 500 (an int)",
     lambda: (target.NOTIFIED_KEYS_CAP, type(target.NOTIFIED_KEYS_CAP).__name__),
     (500, "int")),
    # Regression half: prior-slice API must still be importable alongside the
    # new constants.
    ("prior-slice functions still present",
     lambda: all(callable(getattr(target, n)) for n in
                 ("select_results", "run_cycle", "search_seats_aero", "get_trip")),
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
