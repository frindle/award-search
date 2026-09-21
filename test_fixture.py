"""Adversarial fixture for: aw-sched-runner-s15-first-evaluate-passes-fi

The target's relative imports need a package context, and the sibling modules
(alert_filters, deeplinks, pushover, seats_aero, scheduled_searches) are out of
this slice's scope -- so we register a synthetic `src` package plus recording
stubs in sys.modules BEFORE exec'ing the file. The fake passes_filters records
every (result, filters) pair it is called with and can be switched into
reject/raise modes per case. That record is what lets us assert HOW select_results
evaluates: on a COPY with taxes=0.0 and the filters dict MINUS 'max_taxes'.

Each case: (description, callable_returning_actual, expected)
"""
import importlib.util
import sys
import types


def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m


# --- recording fake for passes_filters ---------------------------------------
RECORD = []  # list of (result_seen, filters_seen) snapshots, call order
MODE = {"mode": "pass"}


def _fake_passes_filters(result, filters):
    RECORD.append((dict(result or {}), dict(filters or {})))
    if MODE["mode"] == "reject_all":
        return False
    if MODE["mode"] == "raise":
        raise RuntimeError("boom")
    if MODE["mode"] == "reject_badprog" and (result or {}).get("program") == "badprog":
        return False
    return True


# --- synthetic package so the target's relative imports resolve --------------
_pkg = types.ModuleType("src")
_pkg.__path__ = ["src"]
sys.modules["src"] = _pkg
_stub("src.alert_filters", passes_filters=_fake_passes_filters)
_stub("src.deeplinks", seats_aero_url=lambda *a, **k: "")
_stub("src.pushover", send_award_notification=lambda *a, **k: None)


class _FakeClient:
    def search(self, *a, **k):
        return []

    def get_trip(self, availability_id):
        return None


_stub("src.seats_aero", SeatsAeroClient=_FakeClient)
_stub("src.scheduled_searches",
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
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["src.scheduled_runner"] = target
spec.loader.exec_module(target)


def _reset(mode="pass"):
    RECORD.clear()
    MODE["mode"] = mode


FILTERS = {"max_taxes": 5.0, "min_miles": 1}
RESULT = {"taxes": 99.0, "program": "ua"}


def _case_first_pass_args():
    _reset()
    target.select_results({"filters": FILTERS}, [dict(RESULT)])
    res, flt = RECORD[-1]
    return (res.get("taxes"), "max_taxes" in flt, flt.get("min_miles"))


def _case_original_not_mutated():
    _reset()
    r = dict(RESULT)
    target.select_results({"filters": FILTERS}, [r])
    return r["taxes"]


def _case_rejection_excludes_result():
    _reset("reject_all")
    kept = target.select_results({"filters": FILTERS}, [dict(RESULT)])
    return (kept, len(RECORD))


def _case_filters_without_max_taxes_pass_through():
    _reset()
    kept = target.select_results({"filters": {"min_miles": 10}}, [dict(RESULT)])
    res, flt = RECORD[-1]
    return (flt, res.get("taxes"), len(kept))


def _case_exception_swallowed():
    _reset("raise")
    kept = target.select_results({"filters": FILTERS}, [dict(RESULT)])
    return kept


def _case_mixed_results_only_passing_kept():
    _reset("reject_badprog")
    good = {"taxes": 3.0, "program": "dl"}
    bad = {"taxes": 4.0, "program": "badprog"}
    kept = target.select_results({"filters": FILTERS}, [good, bad])
    return (kept, len(RECORD))


# Model-drafted; NOT yet read by a human.
DRAFT_UNCONFIRMED = True

CASES = [
    ("first pass sees a copy with taxes=0.0 and filters MINUS 'max_taxes'",
     _case_first_pass_args, (0.0, False, 1)),
    ("the original result dict is not mutated by the first-pass evaluation",
     _case_original_not_mutated, 99.0),
    ("a first-pass rejection excludes the result from kept output",
     _case_rejection_excludes_result, ([], 1)),
    ("filters without 'max_taxes' pass through unchanged; result still kept",
     _case_filters_without_max_taxes_pass_through, ({"min_miles": 10}, 0.0, 1)),
    ("a passes_filters exception is swallowed and the result skipped",
     _case_exception_swallowed, []),
    ("mixed results: only first-pass passers are kept, every result evaluated",
     _case_mixed_results_only_passing_kept, ([{"taxes": 3.0, "program": "dl"}], 2)),
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
