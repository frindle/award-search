"""Adversarial fixture for: aw-scheduled_runner module-level logging

The target uses relative imports (`from .alert_filters import ...`), so it can
only execute inside a package context. We register a stub `src` package (whose
__path__ points at the real src/ dir, so the sibling modules resolve) and bind
the loaded module under BOTH "target" (what this file's API expects) and its
real dotted name (so relative imports find their parent).

Cases separate "did the job" from "made the test go green":
  * log is a real stdlib Logger named after the module (__name__), not print()
    or a function-local logger
  * the swallow-and-continue paths that used to drop work SILENTLY now emit a
    record on THAT logger (a plausible wrong fix -- logging via `print`, a
    differently-named logger, or no call at all -- fails these)
  * regression half: filtering/selection and cycle behaviour are unchanged
"""
import importlib.util
import logging
import os
import sys
import types
from unittest import mock

# --- package context for the relative imports -------------------------------
_pkg = types.ModuleType("src")
_pkg.__path__ = ["src"]
sys.modules.setdefault("src", _pkg)

# `scheduled_searches` is a sibling slice's module and may not exist in this
# worktree yet. Stub it (no-op functions) so the target loads; nothing under
# test here calls into it.
if not os.path.exists("src/scheduled_searches.py"):
    _ss = types.ModuleType("src.scheduled_searches")
    for _n in ("effective_programs", "is_due", "load_schedules",
               "query_legs", "upsert_schedule"):
        setattr(_ss, _n, lambda *a, **k: None)
    sys.modules["src.scheduled_searches"] = _ss

spec = importlib.util.spec_from_file_location(
    "src.scheduled_runner", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC under both names: the fixture API reads `target`, and
# relative imports resolve through sys.modules["src"].
sys.modules["target"] = target
sys.modules["src.scheduled_runner"] = target
spec.loader.exec_module(target)


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def _captured(fn):
    """Run fn with a capture handler on the module logger; return (result, records)."""
    cap = _Capture()
    target.log.addHandler(cap)
    try:
        result = fn()
    finally:
        target.log.removeHandler(cap)
    return result, cap.records


class _Trip:
    total_taxes = 123.45     # select_results uses trip.total_taxes verbatim
    taxes_currency = "USD"
    carriers = ["AA"]


def _good_result():
    return {"availability_id": "a1", "origin": "JFK", "destination": "LHR",
            "date": "2026-07-01", "cabin": "business"}


def _raise(*_a, **_k):
    raise ValueError("boom")


# --- cases ------------------------------------------------------------------

def case_logger_identity():
    return (isinstance(target.log, logging.Logger),
            target.log.name == "src.scheduled_runner")


def case_select_logs_bad_result():
    def run():
        with mock.patch.object(target, "passes_filters", lambda c, f: True), \
             mock.patch.object(target, "seats_aero_url",
                               lambda o, d, dt, cb: "https://seats.example/book"), \
             mock.patch.object(target, "get_trip",
                               side_effect=ValueError("boom")):
            return target.select_results(
                {"filters": {}}, [_good_result(), dict(_good_result(), availability_id="bad")])
    result, records = _captured(run)
    return (result, bool(records), any("select_results" in r.getMessage() for r in records))


def case_run_cycle_logs_failing_alert():
    def run():
        with mock.patch.object(target, "passes_filters", lambda c, f: True), \
             mock.patch.object(target, "seats_aero_url",
                               lambda o, d, dt, cb: "https://seats.example/book"), \
             mock.patch.object(target, "get_trip", return_value=_Trip()):
            def search(a):
                if a.get("broken"):
                    raise RuntimeError("search down")
                return [_good_result()]
            return target.run_cycle({"ok": {}, "bad": {"broken": True}}, search)
    result, records = _captured(run)
    return (result, bool(records), any("run_cycle" in r.getMessage() for r in records))


def case_get_trip_none_on_error():
    with mock.patch.object(target, "SeatsAeroClient", side_effect=OSError("network down")):
        return target.get_trip("a1")


def case_select_keeps_passing_result():
    with mock.patch.object(target, "passes_filters", lambda c, f: True), \
         mock.patch.object(target, "seats_aero_url",
                           lambda o, d, dt, cb: "https://seats.example/book?c=" + cb), \
         mock.patch.object(target, "get_trip", return_value=_Trip()):
        return target.select_results({"filters": {}}, [_good_result()])



CASES = [
    ("log is a stdlib Logger named after the module (__name__)",
     case_logger_identity, (True, True)),

    ("select_results drops a bad result AND logs it on the module logger",
     case_select_logs_bad_result, ([], True, True)),

    ("run_cycle skips a failing alert AND logs it on the module logger",
     case_run_cycle_logs_failing_alert,
     ({"ok": [{"availability_id": "a1", "origin": "JFK", "destination": "LHR",
               "date": "2026-07-01", "cabin": "business", "taxes": 123.45,
               "booking_url": "https://seats.example/book"}]}, True, True)),

    ("get_trip still returns None when the client raises (regression)",
     case_get_trip_none_on_error, None),

    ("select_results still keeps a passing result with taxes + booking_url (regression)",
     case_select_keeps_passing_result,
     [{"availability_id": "a1", "origin": "JFK", "destination": "LHR",
       "date": "2026-07-01", "cabin": "business", "taxes": 123.45,
       "booking_url": "https://seats.example/book?c=business"}]),

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
