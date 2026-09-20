"""Adversarial fixture for: aw-sched-runner-s10-search-schedule

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


# The target module does relative imports of sibling modules that are not part
# of this slice. Stub them in sys.modules BEFORE exec so the module loads; the
# stubs are inert -- search_schedule must work with an injected client and never
# touch SeatsAeroClient itself.
def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


# The target uses RELATIVE imports (from .alert_filters import ...), so it must
# be loaded as a member of the "src" package and its siblings stubbed under the
# absolute names the relative form resolves to.
for _base in ("", "src."):
    _stub(_base + "alert_filters", passes_filters=lambda r, f: True)
    _stub(_base + "deeplinks", seats_aero_url=lambda *a, **k: "")
    _stub(_base + "pushover", send_award_notification=lambda *a, **k: None)
    _stub(_base + "seats_aero", SeatsAeroClient=object)
    _stub(_base + "scheduled_searches",
          effective_programs=lambda *a, **k: [],
          is_due=lambda *a, **k: False,
          load_schedules=lambda *a, **k: {},
          query_legs=lambda *a, **k: [],
          upsert_schedule=lambda *a, **k: None)

spec = importlib.util.spec_from_file_location("src.scheduled_runner", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with the
# task and the dispatch reads as a model failure.
sys.modules[spec.name] = target
spec.loader.exec_module(target)


class FakeClient:
    """Records every search() call; returns RESULTS."""

    def __init__(self):
        self.calls = []

    def search(self, origin, destination, start_date=None, end_date=None,
               cabins=None, programs=None):
        self.calls.append((origin, destination, start_date, end_date,
                           cabins, programs))
        return RESULTS


RESULTS = [
    {"program": "united", "origin": "JFK", "destination": "LAX",
     "date": "2026-10-01", "cabin": "business"},
    {"program": "delta", "origin": "JFK", "destination": "LAX",
     "date": "2026-10-02", "cabin": "economy"},
]

SCHED = {
    "origin": "JFK",
    "destination": "LAX",
    "start_date": "2026-10-01",
    "end_date": "2026-10-31",
    "cabins": ["business"],
    "programs": ["united", "delta"],
}


def _run(sched):
    c = FakeClient()
    out = target.search_schedule(sched, client=c)
    return out, (c.calls[-1] if c.calls else None)


def _propagates():
    class BoomClient:
        def search(self, *a, **k):
            raise RuntimeError("boom")

    try:
        target.search_schedule(SCHED, client=BoomClient())
    except RuntimeError:
        return "raised"
    return "swallowed"


CASES = [
    ("returns the client's results for a full schedule",
     lambda: _run(SCHED)[0],
     RESULTS),

    ("forwards origin/destination/start/end/cabins/programs to client.search",
     lambda: _run(SCHED)[1],
     ("JFK", "LAX", "2026-10-01", "2026-10-31", ["business"],
      ["united", "delta"])),

    ("a None schedule does not raise and still calls search with empty legs",
     lambda: _run(None)[1][:2],
     (None, None)),

    ("an empty dict schedule does not raise and passes None legs through",
     lambda: _run({})[1][:4],
     (None, None, None, None)),

    ("a client that raises propagates the error instead of swallowing it",
     _propagates,
     "raised"),
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
