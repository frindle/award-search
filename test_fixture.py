"""Adversarial fixture for: aw-sched-runner-s5-from-seats-aero-import-s

Property under test (and ONLY this): src/scheduled_runner.py imports
SeatsAeroClient from .seats_aero, and the name is correctly bound through
target's own namespace. Technique (what s1 did, successfully): stub the
imported module with a distinctive fake implementation of the imported name,
load the TARGET module with target.__package__ set so the relative import
resolves to our stub, then assert the imported name is reachable AND correctly
bound by calling it and checking the stub's distinctive return value.

Kill test: remove `from .seats_aero import SeatsAeroClient` from the target ->
case 1 fails (hasattr False) / case 2 raises AttributeError on
target.SeatsAeroClient. A benign implementation that never imports the name
cannot pass cases 1-3; a wrong binding (e.g. importing some other object under
that name, or shadowing it after import) cannot pass case 4's identity check.

The target also does relative imports of sibling modules (.alert_filters,
.deeplinks, .pushover, .scheduled_searches); those are stubbed too so the
module can exec at all -- they are NOT under test and their fakes carry no
assertions.
"""
import sys
import types
import importlib.util

SENTINEL = "AW_FAKE_SEATS_AERO_CLIENT_SENTINEL"
INSTANTIATIONS = []


def _make_stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


class FakeSeatsAeroClient:
    """Distinctive fake of the imported name. Any call through target's
    namespace must land HERE and return SENTINEL -- a real seats_aero
    implementation (or any other object bound to that name) cannot."""

    def __init__(self, *args, **kwargs):
        INSTANTIATIONS.append(self)

    def fetch_fares(self):
        return SENTINEL


fake_seats_aero = _make_stub("src.seats_aero", SeatsAeroClient=FakeSeatsAeroClient)
# Sibling relative imports of the target -- stubbed only so exec_module can run.
_make_stub("src.alert_filters", passes_filters=lambda r, f: True)
_make_stub("src.deeplinks", seats_aero_url=lambda *a, **k: "https://example.invalid/deep")
_make_stub("src.pushover", send_award_notification=lambda *a, **k: None)
_make_stub(
    "src.scheduled_searches",
    effective_programs=lambda *a, **k: [],
    is_due=lambda *a, **k: False,
    load_schedules=lambda *a, **k: {},
    query_legs=lambda *a, **k: [],
    upsert_schedule=lambda *a, **k: None,
)

spec = importlib.util.spec_from_file_location("target", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["target"] = target
# Relative imports resolve against __package__; point it at "src" so
# `from .seats_aero import ...` lands on our stubbed src.seats_aero.
target.__package__ = "src"
spec.loader.exec_module(target)


# Model-drafted; NOT yet read by a human.
DRAFT_UNCONFIRMED = True

CASES = [
    ("imported name is reachable on the target module",
     lambda: hasattr(target, "SeatsAeroClient"), True),
    ("target.SeatsAeroClient IS the stubbed class (correctly bound)",
     lambda: target.SeatsAeroClient is FakeSeatsAeroClient, True),
    ("calling through target's namespace returns the stub's sentinel",
     lambda: target.SeatsAeroClient().fetch_fares(), SENTINEL),
    ("the call went through our stub, not a real implementation",
     lambda: (target.SeatsAeroClient(), len(INSTANTIATIONS) > 0)[1], True),
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
