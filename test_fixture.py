"""Adversarial fixture for: aw-airport-groups-s4-list-groups

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
import importlib.util

spec = importlib.util.spec_from_file_location("target", 'src/airport_groups.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with the
# task and the dispatch reads as a model failure.
sys.modules["target"] = target
spec.loader.exec_module(target)


def _exact_output():
    return target.list_groups()


def _key_set_exact():
    groups = target.list_groups()
    return all(set(g) == {"code", "name", "airports"} for g in groups) and len(groups) > 0


def _no_mutation_of_registry():
    before = dict(target.AIRPORT_GROUPS)
    target.list_groups()
    return target.AIRPORT_GROUPS == before


def _sorted_even_when_insertion_order_differs():
    # A group added LAST must still come FIRST when its code sorts first --
    # an implementation that just iterates AIRPORT_GROUPS in insertion order fails.
    target.AIRPORT_GROUPS["AAA"] = {"name": "Test (AAA)"}
    try:
        groups = target.list_groups()
        return [g["code"] for g in groups] == ["AAA", "JFK", "LHR"] and \
            groups[0]["name"] == "Test (AAA)" and groups[0]["airports"] == ["AAA"]
    finally:
        del target.AIRPORT_GROUPS["AAA"]


CASES = [
    ("exact shape, values and code order for the seeded registry",
     _exact_output,
     [{"code": "JFK", "name": "New York (JFK)", "airports": ["JFK"]},
      {"code": "LHR", "name": "London (LHR)", "airports": ["LHR"]}]),
    ("every entry has exactly the keys code/name/airports", _key_set_exact, True),
    ("list_groups() does not mutate AIRPORT_GROUPS", _no_mutation_of_registry, True),
    ("sorted by code even when insertion order differs (AAA added last)",
     _sorted_even_when_insertion_order_differs, True),
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
