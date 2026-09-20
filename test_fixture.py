"""Adversarial fixture for: aw-sched-runner-s4-from-scheduled-searches

Property under test (and ONLY this): src/scheduled_runner.py imports the five
names from .scheduled_searches and each is correctly bound through target's own
namespace. Technique (same as s1, which passed): stub the imported module with
a distinctive fake implementation of each name, load the TARGET module with
target.__package__ set so the relative import resolves, then call each name via
target.<name> and check the stub's distinctive return value comes back.

Kill test: remove the import line from src/scheduled_runner.py -> every case
below raises AttributeError on target.<name>. A benign/empty implementation of
the five names (or a wrong binding) returns something other than the stub's
sentinel, so it fails too. We deliberately do NOT test run_cycle or any other
behaviour -- that is out of scope for this slice.
"""
import sys
import types
import importlib.util

# --- distinctive fakes ------------------------------------------------------
# Each fake returns a value no real implementation could plausibly produce, so
# the assertion proves the call went through OUR stub (i.e. target.<name> is
# bound to the imported name), not merely that *some* callable exists there.

def _fake_effective_programs(programs):
    return ("FAKE_EFFECTIVE_PROGRAMS", programs)

def _fake_is_due(schedule, now=None):
    return "FAKE_IS_DUE"

def _fake_load_schedules():
    return ["FAKE_SCHEDULE"]

def _fake_query_legs(query):
    return ("FAKE_QUERY_LEGS", query)

def _fake_upsert_schedule(schedule):
    return "FAKE_UPSERTED"

# Stub the module the target imports from. Registered under the ABSOLUTE name
# (src.scheduled_searches) so `from .scheduled_searches import ...` resolves to
# it once target.__package__ == "src".
fake_ss = types.ModuleType("src.scheduled_searches")
fake_ss.effective_programs = _fake_effective_programs
fake_ss.is_due = _fake_is_due
fake_ss.load_schedules = _fake_load_schedules
fake_ss.query_legs = _fake_query_legs
fake_ss.upsert_schedule = _fake_upsert_schedule

# The target also imports from sibling modules (some of which do not exist on
# disk in this worktree). Stub them so the module body executes; we assert
# nothing about them -- they are out of scope for this slice.
for name, attrs in [
    ("src.alert_filters", {"passes_filters": lambda *a: True}),
    ("src.deeplinks", {"seats_aero_url": lambda *a: "FAKE_URL"}),
    ("src.pushover", {"send_award_notification": lambda *a: None}),
]:
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m

sys.modules["src.scheduled_searches"] = fake_ss

# --- load the target --------------------------------------------------------
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
# Relative imports resolve against __package__; set it BEFORE exec_module so
# `from .scheduled_searches import ...` looks up "src.scheduled_searches".
target.__package__ = "src"
spec.loader.exec_module(target)


CASES = [
    ("effective_programs is imported and bound through target's namespace",
     lambda: target.effective_programs(["p1"]),
     ("FAKE_EFFECTIVE_PROGRAMS", ["p1"])),
    ("is_due is imported and bound through target's namespace",
     lambda: target.is_due({"id": "s1"}, now="t0"),
     "FAKE_IS_DUE"),
    ("load_schedules is imported and bound through target's namespace",
     lambda: target.load_schedules(),
     ["FAKE_SCHEDULE"]),
    ("query_legs is imported and bound through target's namespace",
     lambda: target.query_legs({"origin": "SFO"}),
     ("FAKE_QUERY_LEGS", {"origin": "SFO"})),
    ("upsert_schedule is imported and bound through target's namespace",
     lambda: target.upsert_schedule({"id": "s1"}),
     "FAKE_UPSERTED"),
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
