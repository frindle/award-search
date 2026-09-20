"""Adversarial fixture for: aw-sched-runner-s6-seatsaero-client-search-o

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
import importlib.util
from datetime import date

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
spec.loader.exec_module(target)


import requests  # noqa: E402

FULL_ITEM = {
    "id": "avail-1",
    "route": {"originAirport": "JFK", "destinationAirport": "LHR"},
    "date": "2026-10-05",
    "source": "eurobonus",
    "EconomyAvailable": True,
    "EconomyMileageCost": 30000,
    "EconomyRemainingSeats": 4,
    "EconomyAirlines": ["BA"],
    "EconomyDirect": True,
    "BusinessAvailable": False,
    "BusinessMileageCost": None,
    "BusinessRemainingSeats": 0,
    "BusinessAirlines": [],
    "BusinessDirect": False,
}

DEGEN_ITEM = {
    "id": "avail-2",
    "route": {"originAirport": "SFO"},
    "date": "not-a-date",
    "source": "united",
    "EconomyMileageCost": "1,250",
}


class FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class FakeSession:
    """Stands in for requests.Session; records the last .get() call."""

    def __init__(self, payload=None, exc=None):
        self.payload = payload if payload is not None else {"data": []}
        self.exc = exc
        self.last_url = None
        self.last_params = None

    def get(self, url, params=None, timeout=None):
        self.last_url = url
        self.last_params = dict(params or {})
        if self.exc is not None:
            raise self.exc
        return FakeResp(self.payload)


def _client(payload=None, exc=None):
    c = target.SeatsAeroClient(api_key="test-key")
    c.session = FakeSession(payload=payload, exc=exc)
    return c


def _params_case():
    c = _client({"data": []})
    c.search("JFK", "LHR", date(2026, 10, 5), date(2026, 10, 9),
             ["economy", "business"], ["sas", "virgin_atlantic"])
    p = c.session.last_params
    return (p.get("sources"), p.get("start_date"), p.get("end_date"), p.get("cabins"))


CASES = [
    (
        "happy path: full item parses into SeatsAeroAvailability with every cabin attr",
        lambda: (lambda r: (
            type(r[0]).__name__,
            r[0].availability_id,
            r[0].origin,
            r[0].destination,
            r[0].departure_date,
            r[0].source,
            r[0].cabin_avail["economy"],
            r[0].cabin_cost["economy"],
            r[0].cabin_seats["economy"],
            r[0].cabin_airlines["economy"],
            r[0].cabin_direct["economy"],
            r[0].cabin_avail["business"],
            r[0].cabin_cost["business"],
        ))(_client({"data": [FULL_ITEM]}).search("JFK", "LHR", date(2026, 10, 5), date(2026, 10, 9))),
        (
            "SeatsAeroAvailability",
            "avail-1",
            "JFK",
            "LHR",
            date(2026, 10, 5),
            "eurobonus",
            True,
            30000,
            4,
            ["BA"],
            True,
            False,
            0,
        ),
    ),
    (
        "empty data list returns [] (no records, no raise)",
        lambda: _client({"data": []}).search("JFK", "LHR"),
        [],
    ),
    (
        "transport failure (RequestException) returns [] instead of raising",
        lambda: _client(exc=requests.exceptions.ConnectionError("boom")).search("JFK", "LHR"),
        [],
    ),
    (
        "degenerate item: comma cost -> int, missing keys -> defaults, bad date -> None, no raise",
        lambda: (lambda r: (
            r[0].cabin_cost["economy"],
            r[0].cabin_avail["economy"],
            r[0].cabin_seats["economy"],
            r[0].cabin_airlines["economy"],
            r[0].cabin_direct["economy"],
            r[0].departure_date,
            r[0].destination,
        ))(_client({"data": [DEGEN_ITEM]}).search("SFO", "ORD")),
        (1250, False, 0, [], False, None, ""),
    ),
    (
        "programs map to sources and dates/cabins land in the request params",
        lambda: _params_case(),
        ("eurobonus,virginatlantic", "2026-10-05", "2026-10-09", "economy,business"),
    ),
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
