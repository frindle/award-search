"""Adversarial fixture for: aw-sched-runner-s9-result-key

The target module uses relative imports (`from .alert_filters import ...`), so
it cannot be exec'd as a bare file. We register "target" in sys.modules AS A
PACKAGE (with __path__) BEFORE exec_module, and pre-register lightweight stubs
for the sibling modules it imports. This keeps the fixture hermetic: no
network, no credentials file, no dependency on src/__init__.py (which pulls
in cli).

Cases pin down _result_key(r) -> str:
  * canonical form: pipe-joined program|origin|destination|date|cabin
  * degenerate inputs ({}, missing keys) must NOT raise -- absent fields are ""
  * non-string values are coerced with str(), not assumed to be strings
"""
import sys
import types
import importlib.util

# --- stub the sibling modules scheduled_runner.py imports -------------------
def _stub(name, **attrs):
    m = types.ModuleType("target." + name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules["target." + name] = m
    return m

_stub("alert_filters", passes_filters=lambda *a, **k: True)
_stub("deeplinks", seats_aero_url=lambda *a, **k: "https://seats.aero/")
_stub("pushover", send_award_notification=lambda *a, **k: None)
_stub("seats_aero", SeatsAeroClient=object)
_stub("scheduled_searches",
      effective_programs=lambda *a, **k: [],
      is_due=lambda *a, **k: False,
      load_schedules=lambda *a, **k: {},
      query_legs=lambda *a, **k: [],
      upsert_schedule=lambda *a, **k: None)

# --- load the target as a package so its relative imports resolve -----------
spec = importlib.util.spec_from_file_location("target", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
sys.modules["target"] = target          # REGISTER BEFORE EXEC (see scaffold note)
target.__package__ = "target"
target.__path__ = []                    # mark as package: relative imports resolve via sys.modules
spec.loader.exec_module(target)


CASES = [
    ("full record -> canonical pipe-joined key program|origin|destination|date|cabin",
     lambda: target._result_key({
         "program": "united", "origin": "JFK", "destination": "LAX",
         "date": "2026-07-01", "cabin": "business"}),
     "united|JFK|LAX|2026-07-01|business"),

    ("empty dict -> five empty fields joined by pipes, no exception",
     lambda: target._result_key({}),
     "||||"),

    ("missing keys are treated as '' in their fixed positions",
     lambda: target._result_key({"origin": "SFO"}),
     "|SFO|||"),

    ("non-string values coerced with str() (int program, None cabin)",
     lambda: target._result_key({"program": 7, "cabin": None}),
     "7||||None"),

    ("returns a real str for a partial record",
     lambda: type(target._result_key({"destination": "NRT"})).__name__,
     "str"),
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
