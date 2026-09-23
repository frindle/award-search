"""Adversarial fixture for: aw-sched-runner-s19-run-schedule

run_schedule(sched, client=None, notify=True) must:
  * return exactly the list search_schedule() produced (same dicts, same order)
  * call notify_hit() once per result when notify is True -- and NOT at all
    when notify is False
  * survive a notification failure without losing any results
  * let a client.search() exception propagate (a runner that swallows it hides
    outages; search_schedule itself does not catch)

The target module uses relative imports, so it is loaded inside a synthetic
"src" package whose sibling modules are stubs -- the fixture only exercises
run_schedule's own behaviour against an injected client.
"""
import sys
import types
import importlib.util


NOTIF_CALLS = []


def _fake_send(origin, destination, date, program=None, miles=None,
               cabin=None, seats=None, booking_url=None):
    NOTIF_CALLS.append(dict(
        origin=origin, destination=destination, date=date, program=program,
        miles=miles, cabin=cabin, seats=seats, booking_url=booking_url))
    return True


def _boom(*a, **k):
    raise RuntimeError("pushover down")


def _install_stub_package():
    pkg = types.ModuleType("src")
    pkg.__path__ = ["src"]
    sys.modules["src"] = pkg

    stubs = {
        "alert_filters": {"passes_filters": lambda *a, **k: True},
        "deeplinks": {"seats_aero_url": lambda *a, **k: "https://example"},
        # send_award_notification must exist so the target's module-level
        # `from .pushover import send_award_notification` succeeds; each case
        # then rebinds target.send_award_notification to _fake_send / _boom.
        "pushover": {"send_award_notification": lambda *a, **k: None},
        "seats_aero": {"SeatsAeroClient": object},
        "scheduled_searches": {
            "effective_programs": None, "is_due": None, "load_schedules": None,
            "query_legs": None, "upsert_schedule": None,
        },
    }
    for name, attrs in stubs.items():
        m = types.ModuleType("src." + name)
        for k, v in attrs.items():
            setattr(m, k, v)
        sys.modules["src." + name] = m


_install_stub_package()

spec = importlib.util.spec_from_file_location("src.scheduled_runner", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC (see scaffold note): the module must be in sys.modules
# under its package-qualified name before exec_module runs.
sys.modules["src.scheduled_runner"] = target
spec.loader.exec_module(target)


NOTIF_CALLS = []


def _fake_send(origin, destination, date, program=None, miles=None,
               cabin=None, seats=None, booking_url=None):
    NOTIF_CALLS.append(dict(
        origin=origin, destination=destination, date=date, program=program,
        miles=miles, cabin=cabin, seats=seats, booking_url=booking_url))
    return True


def _boom(*a, **k):
    raise RuntimeError("pushover down")


class FakeClient:
    def __init__(self, results=None, exc=None):
        self.results = list(results or [])
        self.exc = exc

    def search(self, origin, destination, start_date=None, end_date=None,
               cabins=None, programs=None):
        if self.exc is not None:
            raise self.exc
        return list(self.results)


SCHED = {"origin": "JFK", "destination": "LAX", "start_date": "2026-10-01",
         "end_date": "2026-10-31", "cabins": ["business"], "programs": ["united"]}

R1 = {"source": "united", "cost": 45000, "cabin": "business",
      "seats": 3, "booking_url": "https://book/1"}
R2 = {"source": "delta", "cost": 60000, "cabin": "first",
      "seats": 1, "booking_url": "https://book/2"}


def _reset():
    NOTIF_CALLS.clear()
    target.send_award_notification = _fake_send


def _expect_raise(fn):
    try:
        fn()
        return "no-raise"
    except Exception as e:
        return type(e).__name__


def _case1():
    _reset()
    return (target.run_schedule(SCHED, client=FakeClient([R1, R2])),
            list(NOTIF_CALLS))


def _case2():
    _reset()
    return (target.run_schedule(SCHED, client=FakeClient([R1]), notify=False),
            list(NOTIF_CALLS))


def _case3():
    _reset()
    return (target.run_schedule(SCHED, client=FakeClient([])),
            len(NOTIF_CALLS))


def _case4():
    _reset()
    setattr(target, "send_award_notification", _boom)
    return target.run_schedule(SCHED, client=FakeClient([R1, R2]))


def _case5():
    return _expect_raise(lambda: target.run_schedule(
        SCHED, client=FakeClient(exc=RuntimeError("api down"))))


def _case6():
    _reset()
    return (target.run_schedule({}, client=FakeClient([R1])),
            len(NOTIF_CALLS))


CASES = [
    ("returns the client's results and notifies once per result",
     _case1,
     ([dict(R1), dict(R2)],
      [{"origin": "JFK", "destination": "LAX", "date": None, "program": "united",
        "miles": 45000, "cabin": "business", "seats": 3,
        "booking_url": "https://book/1"},
       {"origin": "JFK", "destination": "LAX", "date": None, "program": "delta",
        "miles": 60000, "cabin": "first", "seats": 1,
        "booking_url": "https://book/2"}])),

    ("notify=False suppresses every notification but still returns results",
     _case2, ([dict(R1)], [])),

    ("empty result set -> empty list, zero notifications",
     _case3, ([], 0)),

    ("a notification failure must not lose any results",
     _case4, [dict(R1), dict(R2)]),

    ("client.search() raising propagates (runner must not swallow it)",
     _case5, "RuntimeError"),

    ("degenerate sched={} still runs the search and returns its results",
     _case6, ([dict(R1)], 1)),
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
