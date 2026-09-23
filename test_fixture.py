"""Adversarial fixture for: aw-sched-runner-s22-then-union-the-new-keys

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

# The target uses relative imports (`from .alert_filters import ...`), so it
# must load inside a package context. Register a bare `src` package and stub
# the sibling modules BEFORE exec: this keeps the fixture hermetic (no network,
# no credentials files) while still exercising the real scheduled_runner code.
_pkg = types.ModuleType("src")
_pkg.__path__ = []
sys.modules["src"] = _pkg


def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m


_stub("src.alert_filters", passes_filters=lambda candidate, filters: True)
_stub("src.deeplinks", seats_aero_url=lambda *a, **k: "https://seats.aero/x")
_stub("src.pushover", send_award_notification=lambda *a, **k: True)


class _StubClient:
    def search(self, *a, **k):
        return []

    def get_trip(self, availability_id):
        return None


_stub("src.seats_aero", SeatsAeroClient=_StubClient)
_stub(
    "src.scheduled_searches",
    effective_programs=lambda *a, **k: [],
    is_due=lambda *a, **k: False,
    load_schedules=lambda *a, **k: {},
    query_legs=lambda *a, **k: [],
    upsert_schedule=lambda *a, **k: None,
)

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


class _FakeClient:
    """Stands in for SeatsAeroClient; search() returns canned results."""

    def __init__(self, results):
        self._results = results

    def search(self, *a, **kw):
        return list(self._results)


def _res(tag):
    # A result whose identity under target._result_key is a deterministic 5-field key.
    return {"program": tag, "origin": "JFK", "destination": "LAX",
            "date": "2026-12-01", "cabin": "business"}


def _key(tag):
    # The exact string target._result_key produces for _res(tag).
    return "|".join([tag, "JFK", "LAX", "2026-12-01", "business"])


def _run(sched, results):
    """Run run_schedule with a stubbed client; return (results_returned, sched)."""
    s = dict(sched)  # run_schedule mutates the dict it is given
    target.SeatsAeroClient = lambda: _FakeClient(results)
    try:
        returned = target.run_schedule(s, notify=True)
    finally:
        del target.SeatsAeroClient
    return (returned, s)


def case_union_adds_new_keys():
    """New keys are unioned into existing notified_keys, sorted."""
    sched = {"notified_keys": [_key("b"), _key("d")]}
    results = [_res("a"), _res("c")]
    _, s = _run(sched, results)
    return s["notified_keys"]


def case_old_keys_survive():
    """A plausible wrong fix (overwrite instead of union) drops old keys."""
    sched = {"notified_keys": ["old1", "old2"]}
    results = [_res("new")]
    _, s = _run(sched, results)
    return sorted(k for k in s["notified_keys"] if k.startswith("old"))


# Fallback so the fixture still LOADS at the stub baseline (where the constant
# does not exist yet); a correct implementation defines it as 200.
CAP = getattr(target, "NOTIFIED_KEYS_CAP", 200)


def case_cap_trims_to_last():
    """Union beyond NOTIFIED_KEYS_CAP keeps only the LAST (largest) keys."""
    cap = CAP
    old = ["z{:03d}".format(i) for i in range(cap)]          # all survive: largest
    new = [_res("a{:03d}".format(i)) for i in range(5)]      # smallest: trimmed away
    _, s = _run({"notified_keys": old}, new)
    return (len(s["notified_keys"]), s["notified_keys"] == sorted(old)[-cap:])


def case_missing_key_does_not_raise():
    """sched with no notified_keys at all must not raise."""
    results = [_res("k1"), _res("k2")]
    _, s = _run({}, results)
    return s.get("notified_keys")


def case_none_value_does_not_raise():
    """sched['notified_keys'] = None (degenerate stored value) must not raise."""
    results = [_res("k1")]
    _, s = _run({"notified_keys": None}, results)
    return s.get("notified_keys")


def case_return_value_unchanged():
    """Regression: run_schedule still returns ALL results, even when capped."""
    cap = CAP
    results = [_res("r{:03d}".format(i)) for i in range(cap + 10)]
    returned = _run({"notified_keys": []}, results)[0]
    return len(returned)



CASES = [
    ("new keys union into existing notified_keys, sorted",
     case_union_adds_new_keys, [_key("a"), _key("b"), _key("c"), _key("d")]),
    ("old notified_keys survive a new search (union, not overwrite)",
     case_old_keys_survive, ["old1", "old2"]),
    ("union beyond NOTIFIED_KEYS_CAP keeps only the LAST keys",
     case_cap_trims_to_last, (CAP, True)),
    ("sched without notified_keys does not raise; new keys recorded",
     case_missing_key_does_not_raise, [_key("k1"), _key("k2")]),
    ("notified_keys=None does not raise; new keys recorded",
     case_none_value_does_not_raise, [_key("k1")]),
    ("run_schedule still returns all results even when capped",
     case_return_value_unchanged, CAP + 10),
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
