"""Adversarial fixture for: aw-sched-runner-s3-from-pushover-import-sen

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
import pathlib
from unittest import mock

# The target uses RELATIVE imports (`from .pushover import ...`), so it cannot
# be loaded as a bare top-level module -- the scaffold's original loader dies
# with "attempted relative import with no known parent package". Load it as
# `src.scheduled_runner` under a stub `src` package (no __init__ execution:
# src/__init__.py pulls in cli, which is out of scope for this task).
_PKG = types.ModuleType("src")
_PKG.__path__ = [str(pathlib.Path(__file__).resolve().parent / "src")]
sys.modules["src"] = _PKG

# `src/alert_filters.py` is not part of this worktree, but the target imports it
# at module level (pre-existing code). Stub it so the import resolves; every
# case below patches passes_filters anyway.
_AF = types.ModuleType("src.alert_filters")
_AF.passes_filters = lambda r, f: True
sys.modules["src.alert_filters"] = _AF

import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "src.scheduled_runner", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so dataclasses/annotations lookups through sys.modules fail at
# import time for reasons that have nothing to do with the task.
sys.modules["src.scheduled_runner"] = target
_PKG.scheduled_runner = target
spec.loader.exec_module(target)


def _full_result():
    return {
        "origin": "JFK", "destination": "LHR", "date": "2026-10-01",
        "program": "BA", "miles": 35000, "cabin": "business", "seats": 4,
        "booking_url": "https://book.example/LHR",
    }


def _notify_with_fake(fake):
    """Run target.notify_result under a patched send_award_notification and
    return (return_value, kwargs_seen) so cases can assert both."""
    with mock.patch("src.scheduled_runner.send_award_notification", fake):
        ret = target.notify_result(_full_result())
    call = fake.call_args.kwargs if fake.call_args else {}
    return (ret, call)


def _cycle(kept_filters, search_results, search_raises=False):
    """Run one run_cycle with passes_filters and the notifier patched; return
    (out_dict, notification_kwargs_list)."""
    calls = []

    def fake_notify(**kw):
        calls.append(kw)
        return True

    alerts = {"a1": {"filters": {}}}
    search_fn = (lambda a: (_ for _ in ()).throw(RuntimeError("boom"))
                 if search_raises else lambda a: list(search_results))
    with mock.patch("src.scheduled_runner.passes_filters",
                    lambda r, f: kept_filters), \
         mock.patch("src.scheduled_runner.send_award_notification", fake_notify):
        out = target.run_cycle(alerts, search_fn)
    return (out, calls)


CASES = [
    # 1. Happy path: a full result is forwarded field-for-field and the
    #    notification's success propagates as True.
    ("notify_result forwards every field and returns True",
     lambda: _notify_with_fake(mock.Mock(return_value=True)),
     (True, {"origin": "JFK", "destination": "LHR", "date": "2026-10-01",
             "program": "BA", "miles": 35000, "cabin": "business",
             "seats": 4, "booking_url": "https://book.example/LHR"})),

    # 2. Degenerate input: an empty result must NOT raise and must be
     #    normalised (missing miles/seats -> 0, missing url -> None).
    ("notify_result({}) does not raise and normalises to zeros/None",
     _empty_case,
     (True, {"origin": "", "destination": "", "date": "", "program": "",
             "miles": 0, "cabin": "", "seats": 0, "booking_url": None})),

    # 3. Failure path: a transport/credential error inside the notifier must
    #    be swallowed and reported as False -- never raised into run_cycle.
    ("notify_result swallows a RuntimeError from the notifier -> False",
     lambda: _raise_case(),
     (False, {"origin": "JFK", "destination": "LHR", "date": "2026-10-01",
              "program": "BA", "miles": 35000, "cabin": "business",
              "seats": 4, "booking_url": "https://book.example/LHR"})),

    # 4. Regression: run_cycle still returns the kept results per alert and
    #    now notifies exactly once per kept result.
    ("run_cycle keeps results AND sends one notification per kept result",
     lambda: _cycle(True, [_full_result()]),
     ({"a1": [_full_result()]},
      [{"origin": "JFK", "destination": "LHR", "date": "2026-10-01",
        "program": "BA", "miles": 35000, "cabin": "business", "seats": 4,
        "booking_url": "https://book.example/LHR"}])),

    # 5. Boundary: a result that FAILS the filters must be dropped AND must
     #    NOT trigger any notification (catches notify-before-filter).
    ("run_cycle sends no notification for filtered-out results",
     lambda: _cycle(False, [_full_result()]),
     ({}, [])),

    # 6. Failure boundary: a search_fn that raises is skipped as before and
     #    must not send notifications or abort the cycle.
    ("run_cycle skips a raising search_fn without notifying",
     lambda: _cycle(True, [], search_raises=True),
     ({}, [])),
]


def _empty_case():
    fake = mock.Mock(return_value=True)
    with mock.patch("src.scheduled_runner.send_award_notification", fake):
        ret = target.notify_result({})
    call = fake.call_args.kwargs if fake.call_args else {}
    return (ret, call)


def _raise_case():
    def boom(**kw):
        raise RuntimeError("pushover down")

    with mock.patch("src.scheduled_runner.send_award_notification", boom):
        ret = target.notify_result(_full_result())
    return (ret, {"origin": "JFK", "destination": "LHR", "date": "2026-10-01",
                  "program": "BA", "miles": 35000, "cabin": "business",
                  "seats": 4, "booking_url": "https://book.example/LHR"})


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
