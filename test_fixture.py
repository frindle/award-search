"""Adversarial fixture for: aw-sched-runner-s1-from-alert-filters-impor

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


# src/alert_filters.py is provided by the runtime, not this worktree; inject a
# faithful stand-in so `from .alert_filters import passes_filters` resolves when
# the target is loaded as a top-level module. Contract (see TASK.md): every key
# in filters must equal the result's value for that key; an empty filter set
# keeps everything; wrong argument types raise TypeError -- which is exactly
# what separates `passes_filters(r, filters)` from the inverted call order.
def _passes_filters(result, filters):
    if not isinstance(result, dict) or not isinstance(filters, dict):
        raise TypeError("passes_filters expects (result_dict, filters_dict)")
    for k, v in filters.items():
        if result.get(k) != v:
            return False
    return True


_pkg = types.ModuleType("src")
_pkg.__path__ = []
sys.modules.setdefault("src", _pkg)
_af = types.ModuleType("src.alert_filters")
_af.passes_filters = _passes_filters
sys.modules["src.alert_filters"] = _af

spec = importlib.util.spec_from_file_location("target", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# Resolve `from .alert_filters ...` against the injected package: CPython looks
# up globals['__package__'] first when computing the relative-import base.
target.__package__ = "src"
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["target"] = target
spec.loader.exec_module(target)


R1 = {"date": "2024-06-15", "source": "united", "cabin": "business", "cost": 60000}
R2 = {"date": "2024-06-15", "source": "delta", "cabin": "economy", "cost": 35000}
R3 = {"date": "2024-07-01", "source": "united", "cabin": "business", "cost": 90000}


def _search(alert):
    if alert.get("id") == "boom":
        raise RuntimeError("search exploded")
    return [R1, R2]



CASES = [
    ("filters keep only matching results, in original order",
     lambda: target.select_results({"id": "a1", "filters": {"cabin": "business"}}, [R2, R1, R3]),
     [R1, R3]),
    ("missing filters key means no restrictions (all kept)",
     lambda: target.select_results({"id": "a2"}, [R1, R2]),
     [R1, R2]),
    ("None filters treated as empty",
     lambda: target.select_results({"id": "a3", "filters": None}, [R2]),
     [R2]),
    ("malformed results dropped without raising (inverted call order must fail here)",
     lambda: target.select_results({"id": "a4", "filters": {"cabin": "business"}}, ["not-a-dict", R1, 42]),
     [R1]),
    ("empty result list -> empty kept list",
     lambda: target.select_results({"id": "a5", "filters": {}}, []),
     []),
    ("run_cycle keeps only alerts with passing results",
     lambda: target.run_cycle(
         {"a1": {"id": "a1", "filters": {"cabin": "business"}},
          "a2": {"id": "a2", "filters": {"source": "jetblue"}}},
         _search),
     {"a1": [R1]}),
    ("run_cycle skips an alert whose search raises, keeps the rest",
     lambda: target.run_cycle({"boom": {"id": "boom"}, "ok": {"id": "ok"}}, _search),
     {"ok": [R1, R2]}),
    ("run_cycle with no alerts -> {}",
     lambda: target.run_cycle({}, _search),
     {}),
    ("run_cycle with None alerts -> {}",
     lambda: target.run_cycle(None, _search),
     {}),
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
