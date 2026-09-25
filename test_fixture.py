"""Adversarial fixture for: aw-scheduled-searches-store

>>> THE ONE THING THE GENERATOR CANNOT WRITE FOR YOU <<<

CASES is empty and the verify FAILS until you fill it in. That is deliberate.
A generator can emit a verify that DISCRIMINATES (fails at baseline, passes on
a fix). It cannot decide whether the verify is RELEVANT -- whether it tests
the property the task actually asked for. A benign case passes broken work.

Pick inputs that separate "did the job" from "made the test go green":
  * the exact boundary the defect is about, and one on each side of it
  * the degenerate inputs (missing key, None, empty, wrong type) that must NOT
    raise
  * at least one case that a plausible WRONG fix would fail
  * the regression half: things that already work and must keep working

Each case: (description, callable_returning_actual, expected)
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location("target", 'src/scheduled_searches.py')
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

FILE = Path('data/scheduled_searches.json')


def _wipe():
    """Start each case from a clean store so cases don't leak into each other."""
    if FILE.exists():
        FILE.unlink()


def _on_disk():
    return json.loads(FILE.read_text())



CASES = [
    # --- load_schedules -----------------------------------------------------
    ("missing file -> [] (never raises)",
     lambda: (_wipe(), target.load_schedules())[1], []),

    ("unreadable JSON -> [] with a warning, not an exception",
     lambda: (FILE.parent.mkdir(parents=True, exist_ok=True),
              FILE.write_text("{not json"),
              target.load_schedules())[-1], []),

    ("load returns a LIST of records, not the keyed dict",
     lambda: list((_wipe(),
                   target.upsert_schedule({"id": "a", "enabled": True}),
                   type(target.load_schedules()).__name__,
                   len(target.load_schedules())))[2:], ["list", 1]),

    # --- upsert / save ------------------------------------------------------
    ("upsert inserts a new record; on-disk shape is keyed by id like alerts.json",
     lambda: (_wipe(),
              target.upsert_schedule({"id": "s1", "programs": ["AA"]}),
              _on_disk())[-1], {"s1": {"id": "s1", "programs": ["AA"]}}),

    ("upsert replaces in place when the id exists, leaving other records untouched",
     lambda: (_wipe(),
              target.upsert_schedule({"id": "s1", "note": "old"}),
              target.upsert_schedule({"id": "s2", "note": "keep"}),
              target.upsert_schedule({"id": "s1", "note": "new"}),
              _on_disk())[-1],
     {"s1": {"id": "s1", "note": "new"}, "s2": {"id": "s2", "note": "keep"}}),

    ("save_schedules writes atomically: no .json.tmp sibling left behind, file valid",
     lambda: (_wipe(),
              target.save_schedules({"x": {"id": "x"}}),
              sorted(p.name for p in FILE.parent.iterdir() if 'scheduled' in p.name))[-1],
     ["scheduled_searches.json"]),

    # --- is_due -------------------------------------------------------------
    ("disabled record (enabled=False) is never due, even with stale last_checked",
     lambda: target.is_due({"id": "d", "enabled": False,
                            "last_checked": (datetime.now() - timedelta(days=9)).isoformat()}),
     False),

    ("enabled key absent defaults to enabled; no last_checked -> due now",
     lambda: target.is_due({"id": "n"}), True),

    ("unparseable last_checked -> treated as never checked, due (no raise)",
     lambda: target.is_due({"id": "u", "last_checked": "yesterday-ish"}), True),

    ("within the default 6h interval -> not yet due",
     lambda: target.is_due({"id": "r",
                            "last_checked": (datetime.now() - timedelta(hours=2)).isoformat()}),
     False),

    ("past the default 6h interval -> due",
     lambda: target.is_due({"id": "o",
                            "last_checked": (datetime.now() - timedelta(hours=7)).isoformat()}),
     True),

    ("custom interval_hours is honoured, not the default (20min < 30min -> not due)",
     lambda: target.is_due({"id": "c", "interval_hours": 0.5,
                            "last_checked": (datetime.now() - timedelta(minutes=20)).isoformat()}),
     False),

    ("custom interval shorter than the default flips a record that would be not-due under 6h",
     lambda: target.is_due({"id": "c2", "interval_hours": 0.5,
                            "last_checked": (datetime.now() - timedelta(minutes=40)).isoformat()}),
     True),

    # --- effective_programs -------------------------------------------------
    ("programs deduplicated with original order preserved",
     lambda: target.effective_programs({"id": "p", "programs": ["BB", "AA", "BB", "CC"]}),
     ["BB", "AA", "CC"]),

    ("missing programs -> [] (no raise)",
     lambda: target.effective_programs({"id": "p"}), []),

    # --- query_legs ---------------------------------------------------------
    ("2 origins x 2 destinations x 1 range -> 4 legs with the right keys/values",
     lambda: target.query_legs({
         "origins": ["JFK", "LAX"],
         "destinations": ["CDG", "NRT"],
         "date_ranges": [{"start": "2026-05-01", "end": "2026-05-31"}],
     }),
     [
         {"origin": "JFK", "destination": "CDG", "start_date": "2026-05-01", "end_date": "2026-05-31"},
         {"origin": "JFK", "destination": "NRT", "start_date": "2026-05-01", "end_date": "2026-05-31"},
         {"origin": "LAX", "destination": "CDG", "start_date": "2026-05-01", "end_date": "2026-05-31"},
         {"origin": "LAX", "destination": "NRT", "start_date": "2026-05-01", "end_date": "2026-05-31"},
     ]),

    ("range spelled start_date/end_date is normalised onto the leg keys",
     lambda: target.query_legs({
         "origins": ["SFO"],
         "destinations": ["LHR"],
         "date_ranges": [{"start_date": "2026-06-10", "end_date": "2026-07-01"}],
     }),
     [{"origin": "SFO", "destination": "LHR", "start_date": "2026-06-10", "end_date": "2026-07-01"}]),

    ("any of the three inputs missing or empty -> [] (no raise)",
     lambda: [target.query_legs({"origins": ["JFK"]}),
              target.query_legs({"origins": [], "destinations": ["CDG"],
                                "date_ranges": [{"start": "a", "end": "b"}]}),
              target.query_legs({})],
     [[], [], []]),

    # --- regression: the runner's import line must resolve ------------------
    ("all five names the runner imports at module scope exist and are callable",
     lambda: [callable(getattr(target, n)) for n in
              ("effective_programs", "is_due", "load_schedules", "query_legs", "upsert_schedule")],
     [True] * 5),
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
    _wipe()
    print("  {}/{} case(s) passed".format(len(CASES) - fails, len(CASES)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
