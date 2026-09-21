"""Adversarial fixture for: aw-sched-runner-s11-client-none-seatsaerocli

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
import importlib.util


# The target uses relative imports (`from .seats_aero import SeatsAeroClient`).
# Loaded standalone it has no package context, so give it one: register a fake
# `src` package and stub the sibling modules under their dotted names BEFORE
# exec. We must NOT import the real package -- `src/__init__.py` pulls in `.cli`.
class _FakeSeatsAeroClient:
    instances = []

    def __init__(self):
        self.search_calls = []
        type(self).instances.append(self)

    def search(self, *args):
        self.search_calls.append(args)
        return [{"program": "stub", "n": len(args)}]


def _install_stub(dotted_name, **attrs):
    mod = types.ModuleType(dotted_name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[dotted_name] = mod
    return mod


_pkg = types.ModuleType("src")
_pkg.__path__ = []
sys.modules["src"] = _pkg

_install_stub("src.alert_filters", passes_filters=lambda r, f: True)
_install_stub("src.deeplinks", seats_aero_url=lambda *a: "url")
_install_stub("src.pushover", send_award_notification=lambda *a, **k: None)
_install_stub("src.seats_aero", SeatsAeroClient=_FakeSeatsAeroClient)
_install_stub(
    "src.scheduled_searches",
    effective_programs=lambda *a: [],
    is_due=lambda *a: False,
    load_schedules=lambda *a: {},
    query_legs=lambda *a: [],
    upsert_schedule=lambda *a: None,
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
spec.loader.exec_module(target)


SCHED = {
    "origin": "JFK",
    "destination": "LHR",
    "start_date": "2026-10-01",
    "end_date": "2026-10-31",
    "cabins": ["F"],
    "programs": ["AA"],
}


def _reset():
    _FakeSeatsAeroClient.instances = []


class _Explicit:
    def __init__(self):
        self.calls = []

    def search(self, *args):
        self.calls.append(args)
        return [{"explicit": True}]


def case_explicit_client_still_used():
    """Regression half: a passed client must be used as-is (no new default)."""
    _reset()
    c = _Explicit()
    got = target.search_schedule(SCHED, client=c)
    assert len(c.calls) == 1 and c.calls[0] == (
        "JFK", "LHR", "2026-10-01", "2026-10-31", ["F"], ["AA"]), \
        "explicit client.search not called with the six forwarded args"
    assert len(_FakeSeatsAeroClient.instances) == 0, \
        "default SeatsAeroClient must NOT be constructed when a client is passed"
    return got


def case_default_client_used():
    """The defect: client=None (the default) must fall back to SeatsAeroClient."""
    _reset()
    try:
        got = target.search_schedule(SCHED)
    except AttributeError as e:
        raise AssertionError("client=None raised AttributeError: {}".format(e))
    assert len(_FakeSeatsAeroClient.instances) == 1, \
        "expected exactly one SeatsAeroClient instance for the default path"
    inst = _FakeSeatsAeroClient.instances[0]
    assert len(inst.search_calls) == 1 and inst.search_calls[0] == (
        "JFK", "LHR", "2026-10-01", "2026-10-31", ["F"], ["AA"]), \
        "default client.search not called with the six forwarded args"
    return got


def case_default_client_empty_sched():
    """Boundary: empty schedule + default client must forward all-None args."""
    _reset()
    try:
        got = target.search_schedule({})
    except AttributeError as e:
        raise AssertionError("client=None raised AttributeError: {}".format(e))
    assert len(_FakeSeatsAeroClient.instances) == 1, \
        "expected exactly one SeatsAeroClient instance for the default path"
    inst = _FakeSeatsAeroClient.instances[0]
    assert inst.search_calls and inst.search_calls[-1] == (None,) * 6, \
        "empty schedule must forward six None args, got {!r}".format(
            inst.search_calls)
    return got


CASES = [
    ("explicit client is still used as-is", case_explicit_client_still_used,
     [{"explicit": True}]),
    ("client=None falls back to SeatsAeroClient and forwards all six args",
     case_default_client_used,
     [{"program": "stub", "n": 6}]),
    ("client=None with empty schedule forwards six None args",
     case_default_client_empty_sched,
     [{"program": "stub", "n": 6}]),
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
