"""Adversarial fixture for: aw-sched-routes-s7-parse-date-ranges

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
import types

# The target imports two sibling modules (`..scheduled_runner`, `..transfer_partners`)
# that are not part of this slice. Stub them so the module under test loads;
# none of the cases below touch their behaviour.
_PKG = "awtest"
_top = types.ModuleType(_PKG)
_top.__path__ = []
_webui = types.ModuleType(f"{_PKG}.webui")
_webui.__path__ = []
_runner = types.ModuleType(f"{_PKG}.scheduled_runner")
_runner.run_schedule = lambda **kw: {"ran": sorted(kw)}
_partners = types.ModuleType(f"{_PKG}.transfer_partners")
_partners.list_partners = lambda: []
sys.modules[_PKG] = _top
sys.modules[f"{_PKG}.webui"] = _webui
sys.modules[f"{_PKG}.scheduled_runner"] = _runner
sys.modules[f"{_PKG}.transfer_partners"] = _partners

spec = importlib.util.spec_from_file_location(f"{_PKG}.webui.scheduled_routes", 'src/webui/scheduled_routes.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules[spec.name] = target
spec.loader.exec_module(target)


CASES = [
    ("equal-length lists pair positionally",
     lambda: target.parse_date_ranges(["2026-01-05", "2026-02-10"], ["2026-01-09", "2026-02-14"]),
     [{"start": "2026-01-05", "end": "2026-01-09"},
      {"start": "2026-02-10", "end": "2026-02-14"}]),
    ("more starts than ends: missing end is None, not dropped or padded",
     lambda: target.parse_date_ranges(["2026-03-01", "2026-03-15"], ["2026-03-05"]),
     [{"start": "2026-03-01", "end": "2026-03-05"},
      {"start": "2026-03-15", "end": None}]),
    ("more ends than starts: extra ends are ignored, no crash",
     lambda: target.parse_date_ranges(["2026-04-01"], ["2026-04-05", "2026-04-09"]),
     [{"start": "2026-04-01", "end": "2026-04-05"}]),
    ("blank entries are dropped and whitespace stripped before pairing",
     lambda: target.parse_date_ranges([" 2026-05-01 ", "", "   ", "2026-05-20"], ["", "2026-05-03"]),
     [{"start": "2026-05-01", "end": "2026-05-03"},
      {"start": "2026-05-20", "end": None}]),
    ("empty lists yield an empty list, not a raise",
     lambda: target.parse_date_ranges([], []),
     []),
    ("regression: parse_csv from the previous slice still works",
     lambda: target.parse_csv("a, b ,c"),
     ["a", "b", "c"]),
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
