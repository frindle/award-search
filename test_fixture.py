"""Adversarial fixture for: aw-sched-runner-s17-surviving-hits-get-resul

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


# --- load the target as `src.scheduled_runner` so its relative imports resolve.
# The sibling modules this slice does not touch are stubbed in sys.modules;
# src/deeplinks.py is loaded for REAL because the asserted booking_url values
# come from seats_aero_url itself (a plausible wrong fix that hand-rolls a URL
# or drops an argument must fail here).
def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


_pkg = _stub("src")
_pkg.__path__ = []

_stub("src.alert_filters", passes_filters=lambda candidate, filters: True)
_stub("src.pushover", send_award_notification=lambda *a, **k: None)
_stub(
    "src.seats_aero",
    SeatsAeroClient=type("SeatsAeroClient", (), {
        "__init__": lambda self, *a, **k: None,
        "search": lambda self, *a, **k: [],
        "get_trip": lambda self, *a, **k: None,
    }),
)
_stub(
    "src.scheduled_searches",
    effective_programs=lambda *a, **k: [],
    is_due=lambda *a, **k: False,
    load_schedules=lambda *a, **k: {},
    query_legs=lambda *a, **k: [],
    upsert_schedule=lambda *a, **k: None,
)

_dl_spec = importlib.util.spec_from_file_location("src.deeplinks", "src/deeplinks.py")
_deeplinks = importlib.util.module_from_spec(_dl_spec)
sys.modules["src.deeplinks"] = _deeplinks
_dl_spec.loader.exec_module(_deeplinks)

spec = importlib.util.spec_from_file_location("src.scheduled_runner", "src/scheduled_runner.py")
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


def _hit(origin, destination, date, cabin=None):
    r = {"program": "united", "origin": origin, "destination": destination, "date": date}
    if cabin is not None:
        r["cabin"] = cabin
    return r


HIT1 = _hit("jfk", "lax", "2026-07-01", "business")
URL1 = target.seats_aero_url("jfk", "lax", "2026-07-01", "business")

HIT2A = _hit("sfo", "nrt", "2026-08-15", "first")
HIT2B = _hit("ord", "dub", "2026-09-30", "economy")
URL2A = target.seats_aero_url("sfo", "nrt", "2026-08-15", "first")
URL2B = target.seats_aero_url("ord", "dub", "2026-09-30", "economy")

HIT3 = _hit("lhr", "syd", "2026-10-05")  # no cabin key at all
URL3 = target.seats_aero_url("lhr", "syd", "2026-10-05", None)


def case_single_hit():
    out = target.run_cycle({"a1": {"filters": {}}}, lambda alert: [dict(HIT1)])
    want = {"a1": [{**HIT1, "booking_url": URL1}]}
    assert out == want, "single hit must carry its own booking_url"
    # pin the exact deeplinks shape too -- a hand-rolled URL fails here
    assert out["a1"][0]["booking_url"] == (
        "https://seats.aero/search?origins=JFK&destinations=LAX"
        "&start_date=2026-07-01&end_date=2026-07-01"
    ), out["a1"][0]["booking_url"]
    return "ok"


def case_each_hit_own_url():
    hits = [dict(HIT2A), dict(HIT2B)]
    out = target.run_cycle({"a2": {"filters": {}}}, lambda alert: list(hits))
    got = [r["booking_url"] for r in out["a2"]]
    want = [URL2A, URL2B]
    assert got == want, "each hit must get a URL from ITS OWN fields, not one shared/constant URL"
    return "ok"


def case_missing_cabin_key():
    out = target.run_cycle({"a3": {"filters": {}}}, lambda alert: [dict(HIT3)])
    got = out["a3"][0]["booking_url"]
    assert got == URL3, "hit without a cabin key must still get booking_url from origin/destination/date"
    return "ok"


def case_no_hits_absent():
    out = target.run_cycle({"a4": {"filters": {}}}, lambda alert: [])
    assert out == {}, "alert with no surviving hits must not appear in the output"
    return "ok"


def case_raising_search_skipped_others_kept():
    def search_fn(alert):
        if alert.get("tag") == "boom":
            raise RuntimeError("seats.aero down")
        return [dict(HIT1)]

    alerts = {"boom": {"filters": {}, "tag": "boom"}, "fine": {"filters": {}}}
    out = target.run_cycle(alerts, search_fn)
    assert set(out.keys()) == {"fine"}, "a raising alert must be skipped without aborting the cycle"
    assert out["fine"][0]["booking_url"] == URL1
    return "ok"


CASES = [
    ("single surviving hit gets booking_url from its own fields", case_single_hit, "ok"),
    ("each of multiple hits gets a distinct URL (no shared/constant URL)", case_each_hit_own_url, "ok"),
    ("hit missing the cabin key still gets a valid booking_url", case_missing_cabin_key, "ok"),
    ("alert with no surviving hits stays absent from output", case_no_hits_absent, "ok"),
    ("raising search_fn skips that alert but keeps processing others", case_raising_search_skipped_others_kept, "ok"),
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
