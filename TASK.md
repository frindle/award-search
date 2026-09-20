# TASK: aw-sched-runner-s6-seatsaero-client-search-o

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` currently only re-exports `SeatsAeroClient` from the
sibling module (`from .seats_aero import SeatsAeroClient`) and has no self-contained
search implementation of its own. Verified by reading the file: it contains a bare
import plus unrelated helpers, so any consumer that needs the runner's own client
gets nothing runnable in this slice.

## Entry point

`src/scheduled_runner.py` -- the whole module is the entry point; add the
client and dataclass here (no other files).

## Required change

In `src/scheduled_runner.py`, implement a self-contained Seats.aero search:

- A `SeatsAeroAvailability` record with exactly these attributes:
  `availability_id` (str), `origin` (str), `destination` (str),
  `departure_date` (`datetime.date` or None when the API date is missing/invalid),
  `source` (str), and per-cabin dicts keyed by cabin name
  ("economy", "premium", "business", "first"):
  `cabin_avail {cabin: bool}`, `cabin_cost {cabin: int}`,
  `cabin_seats {cabin: int}`, `cabin_airlines {cabin: List[str]}`,
  `cabin_direct {cabin: bool}`.
- A `SeatsAeroClient` class with constructor `__init__(self, api_key=...)` that
  stores the key and a `requests.Session`, and method
  `search(self, origin, destination, start_date=None, end_date=None, cabins=None, programs=None) -> List[SeatsAeroAvailability]`.

Contract for `search`:
- Builds request params: `origin_airport`, `destination_airport`; adds
  `start_date`/`end_date` as ISO strings when given; joins non-empty `cabins`
  with commas into `cabins`; maps each entry of `programs` through a
  program->source table (e.g. "sas" -> "eurobonus", "virgin_atlantic" ->
  "virginatlantic") and joins the known sources with commas into `sources`.
- GETs `{API_BASE}/search` (base URL `https://seats.aero/partnerapi`) via the
  session, with a timeout.
- On any transport/HTTP failure (`requests.exceptions.RequestException`,
  including raised status codes) returns `[]` -- never raises.
- Parses each item of the JSON `data` list into one `SeatsAeroAvailability`:
  `availability_id` from `id`; `origin`/`destination` from
  `route.originAirport` / `route.destinationAirport`; `departure_date` parsed
  with `date.fromisoformat(item["date"])`, falling back to None when the date is
  missing or unparseable; `source` from `source`.
- Per cabin (economy, premium, business, first), read the API fields
  `<Cabin>Available`, `<Cabin>MileageCost`, `<Cabin>RemainingSeats`,
  `<Cabin>Airlines`, `<Cabin>Direct` (cabin name capitalised):
  `cabin_avail[cabin]` is a bool; `cabin_cost[cabin]` is an int -- comma-formatted
  strings like "1,250" must become 1250 and missing/None cost becomes 0;
  `cabin_seats[cabin]` is an int (missing -> 0); `cabin_airlines[cabin]` is a
  list of str (missing -> []); `cabin_direct[cabin]` is a bool.
- An empty `data` list returns `[]`.

Behaviour that must NOT change:
- The module must still import cleanly and expose both `SeatsAeroClient` and
  `SeatsAeroAvailability` at top level (the fixture imports the module by path).
- `search` never raises for transport errors or malformed per-item fields; it
  degrades to defaults (`[]`, 0, False, [], None) instead.

## Must contain

- `class SeatsAeroClient:`
- `def search(`
- `-> List[SeatsAeroAvailability]:`
- `class SeatsAeroAvailability:`
- `cabin_avail: Dict[str, bool]`
- `cabin_cost: Dict[str, int]`
- `cabin_seats: Dict[str, int]`
- `cabin_airlines: Dict[str, List[str]]`
- `cabin_direct: Dict[str, bool]`
- `PROGRAM_TO_SOURCE`

## Scope

Only edit `src/scheduled_runner.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
test_fixture.py is the test fixture -- changing it invalidates the check.

## Keep every changed line exercised (relevance)

After the job runs, a mutation check flips/deletes each line you changed and
asks the verify to catch it. A changed line whose every mutant survives --
because no test asserts it -- FAILS the gate even when the fix is correct, and
the review never runs. So do NOT emit an isolated, untested line:
- Fold an unavoidable constant onto a line the test already exercises. Put a
  `timeout=` / a `daemon=True` flag / a small tuning number on the SAME line as
  a header dict, URL, or argument the fixture checks -- never on its own line.
- Prefer falling through to an implicit `return None` over a standalone
  `return None` in an `except:` the tests do not assert.
- If a line genuinely cannot be asserted and cannot be folded, it usually
  should not be a separate line at all -- restructure so it isn't.
This is not about adding bogus assertions for constants; it is about not
leaving a lone line that carries no tested behaviour.

## Loop instruction

Run `bash verify.sh` after every edit and keep editing until it prints
`VERIFY_OK`.
