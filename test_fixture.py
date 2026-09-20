"""Adversarial fixture for: aw-sched-runner-s7-seatsaeroclient-get-trip

The target module uses relative imports (`from .seats_aero import ...`), so it
cannot be exec'd as a bare file. We register "target" in sys.modules AS A
PACKAGE (with __path__) BEFORE exec_module, and pre-register lightweight stubs
for the sibling modules it imports -- including a fake SeatsAeroClient whose
behaviour each case controls. This keeps the fixture hermetic: no network, no
credentials file, no dependency on src/__init__.py (which pulls in cli).

Cases pin down:
  * delegation: get_trip(availability_id) calls client.get_trip with that id
  * happy path: total_taxes is a float of cents/100; taxes_currency and
    carriers pass through untouched
  * None passthrough: no trip -> None (not {}, not an exception)
  * failure: client raises (e.g. missing API key) -> None, not a crash
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


class _FakeTrip:
    def __init__(self):
        self.total_taxes = 12345          # cents, as the client returns it
        self.taxes_currency = "EUR"
        self.carriers = ["LH", "OS"]


class _FakeClient:
    """Records calls; behaviour is set per-case via .trip / .exc."""
    trip = None
    exc = None
    calls = []

    def __init__(self, *a, **k):
        pass

    def get_trip(self, availability_id, *a, **k):
        type(self).calls.append(availability_id)
        if self.exc is not None:
            raise self.exc
        return self.trip


_stub("seats_aero", SeatsAeroClient=_FakeClient)
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
    ("happy path: total_taxes is float(cents/100), currency+carriers pass through",
     lambda: (lambda t: (t.total_taxes, type(t.total_taxes).__name__,
                         t.taxes_currency, list(t.carriers)))(
         _call("AV-123", trip=_FakeTrip())),
     (123.45, "float", "EUR", ["LH", "OS"])),

    ("delegates the availability_id to SeatsAeroClient.get_trip",
     lambda: (_reset(), _call("AV-777"), _FakeClient.calls)[-1],
     ["AV-777"]),

    ("no trip (client returns None) -> None, not a dict/exception",
     lambda: _call("AV-none", trip=None),
     None),

    ("client raises (e.g. missing API key) -> None, does not crash",
     lambda: _call("AV-boom", exc=ValueError("Seats.aero API key not found")),
     None),
]


def _reset():
    _FakeClient.trip = None
    _FakeClient.exc = None
    _FakeClient.calls = []


def _call(availability_id, trip=None, exc=None):
    _reset()
    _FakeClient.trip = trip
    _FakeClient.exc = exc
    return target.get_trip(availability_id)


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
