"""Adversarial fixture for: aw-sched-runner-s2-from-deeplinks-import-se

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


def _fake_pkg(name, path=None):
    """Register a package module so `from .x import y` inside the target
    resolves without importing the real src/__init__.py (which pulls in
    browser/CLI deps). Setting __path__ lets submodules load from disk."""
    if name not in sys.modules:
        m = types.ModuleType(name)
        m.__package__ = name
        m.__path__ = [str(path)] if path else []
        sys.modules[name] = m
    return sys.modules[name]


def _fake_alert_filters():
    """Deterministic stub for the pre-existing dependency: a result passes iff
    its 'cabin' is in filters['cabins'] (or there are no cabin filters)."""
    if "src.alert_filters" not in sys.modules:
        m = types.ModuleType("src.alert_filters")

        def passes_filters(r, filters):
            cabins = (filters or {}).get("cabins")
            return (not cabins) or (r.get("cabin") in cabins)

        m.passes_filters = passes_filters
        sys.modules["src.alert_filters"] = m
    return sys.modules["src.alert_filters"]


# The target uses RELATIVE imports (`from .alert_filters import ...`,
# `from .deeplinks import ...`), so it must be loaded as a member of the `src`
# package. Register a bare `src` package (NOT its real __init__, which drags in
# browser/CLI deps) whose __path__ points at the real src dir, pre-stub
# alert_filters, and let the REAL deeplinks.py provide seats_aero_url so the URL
# assertions test the actual link builder.
_src_dir = str(pathlib.Path("src").resolve())
_fake_pkg("src", _src_dir)
_af = _fake_alert_filters()

spec = importlib.util.spec_from_file_location(
    "src.scheduled_runner", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["src.scheduled_runner"] = target
spec.loader.exec_module(target)


ALERT = {"origin": "jfk", "destination": "lhr", "date": "2026-10-01"}
RESULTS = [{"cabin": "business"}, {"cabin": "economy"}]

# seats.aero URL the real src/deeplinks.py must produce for ALERT (uppercased,
# quoted, start_date == end_date). A hand-rolled URL builder that forgets to
# uppercase or to set both date params fails this.
EXPECTED_URL = ("https://seats.aero/search?origins=JFK&destinations=LHR"
                "&start_date=2026-10-01&end_date=2026-10-01")


def _linked_urls(alert, results):
    return [r["booking_url"] for r in target.booking_links(alert, results)]


CASES = [
    # happy path: every result gets the exact seats.aero URL built from the alert
    ("every result carries the seats.aero booking_url",
     lambda: _linked_urls(ALERT, RESULTS), [EXPECTED_URL] * 2),

    # boundary: empty results -> no links, not an error
    ("empty results list yields []",
     lambda: target.booking_links(ALERT, []), []),

    # degenerate inputs must NOT raise and must still link with defaults
    ("None alert + None results degrades to one default-cabin link",
     lambda: [r["booking_url"] for r in target.booking_links(None, None)],
     ["https://seats.aero/search?origins=&destinations=&start_date=&end_date="]),

    # missing keys fall back to "" and cabin defaults to "economy" (the literal
    # default the spec pins) -- a wrong fix that passes cabin through as None or
    # omits the default fails this
    ("missing alert keys use '' origin/destination/date and 'economy' cabin",
     lambda: _linked_urls({}, [{"cabin": "business"}]),
     ["https://seats.aero/search?origins=&destinations=&start_date=&end_date="]),

    # inputs are never mutated -- a plausible wrong fix that does
    # r["booking_url"] = ... in place fails this
    ("input results are not mutated",
     lambda: (target.booking_links(ALERT, RESULTS), RESULTS[0].get("booking_url")),
     ([{"cabin": "business", "booking_url": EXPECTED_URL},
       {"cabin": "economy", "booking_url": EXPECTED_URL}], None)),

    # regression half: select_results still filters by the alert's cabin filter
    ("select_results keeps only matching cabins (regression)",
     lambda: target.select_results({"filters": {"cabins": ["business"]}}, RESULTS),
     [{"cabin": "business"}]),

    # regression half: run_cycle still maps alert_id -> kept results and skips
    # alerts whose search_fn raises or that keep nothing
    ("run_cycle keeps matching alerts, drops raising/empty ones (regression)",
     lambda: target.run_cycle(
         {"a1": ALERT, "a2": dict(ALERT, origin="sfo")},
         lambda a: RESULTS if a.get("origin") == "jfk" else (_ for _ in ()).throw(ValueError())),
     {"a1": [{"cabin": "business"}, {"cabin": "economy"}]}),
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
