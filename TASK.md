# TASK: aw-scheduled-searches-store

## Confirmed defect (observed, not suspected)

`src/scheduled_runner.py` imports at module scope `from .scheduled_searches import effective_programs, is_due, load_schedules, query_legs, upsert_schedule`, but no such module exists anywhere in the repo -- `src/scheduled_searches.py` holds only a one-line stub docstring. Importing `src.scheduled_runner` therefore raises ImportError (the stub has none of those names), which makes every downstream slice that touches the runner (aw-app-wiring s7, aw-sched-routes) unsatisfiable.

## Entry point

`src/scheduled_searches.py:1` -- the whole module body is missing; create it per the contract below.

## Required change

Create src/scheduled_searches.py: the persistence+scheduling helper module that src/scheduled_runner.py imports at module scope as 'from .scheduled_searches import effective_programs, is_due, load_schedules, query_legs, upsert_schedule'. Right now that module does not exist anywhere in the repo, so importing src/scheduled_runner.py raises ImportError and every downstream slice (aw-app-wiring s7, aw-sched-routes) is unsatisfiable. Mirror the conventions of the existing src/alerts.py exactly (json file store under DATA_DIR = Path('data'), a threading.Lock, atomic tmp-write + Path.replace, records keyed by their 'id'):

1. Module constants: `DATA_DIR = Path('data')`, `SCHEDULES_FILE = DATA_DIR / 'scheduled_searches.json'`, `DEFAULT_INTERVAL_HOURS = 6.0`.
2. `load_schedules() -> List[Dict]`: return the stored schedule records as a LIST (the runner does `for s in (load_schedules() or [])`); the on-disk shape is a dict keyed by schedule id like alerts.json, so return `list(data.values())`; return [] when the file is missing, empty, or unreadable JSON (log a warning, never raise).
3. `save_schedules(schedules: Dict[str, Dict]) -> None`: atomic write exactly like save_alerts -- under the lock, write to the `.json.tmp` sibling, then `Path.replace`; create DATA_DIR if needed.
4. `upsert_schedule(sched: Dict) -> None`: read the raw keyed dict, set `data[sched['id']] = sched`, save -- insert when new, replace in place when the id already exists, leaving every other record untouched.
5. `is_due(sched: Dict) -> bool`: False when the record is disabled (`enabled` falsy; defaulting to True when the key is absent); otherwise True when 'last_checked' is None/missing/unparseable (never checked -> due now), else True only when `datetime.now() - datetime.fromisoformat(sched['last_checked']) >= (sched.get('interval_hours') or DEFAULT_INTERVAL_HOURS)` hours.
6. `effective_programs(sched: Dict) -> List[str]`: the schedule's own `sched['programs']` deduplicated with original order preserved, [] when missing/empty -- do NOT import any other project module.
7. `query_legs(sched: Dict) -> List[Dict]`: one leg per (origin, destination, date_range) combination from `sched['origins']`, `sched['destinations']` and `sched['date_ranges']` (each range a dict with 'start'/'end' or 'start_date'/'end_date'), each leg a dict with keys origin, destination, start_date, end_date; [] when any of the three inputs is missing or empty.

Use module-level `logging.getLogger(__name__)`. Pure stdlib only: no new third-party dependency and no import of another src/ module.

Behaviour that must NOT change:
- The on-disk store stays a JSON object keyed by schedule id (same shape as data/alerts.json), so existing files written by other code keep loading.
- Writes stay atomic (tmp sibling + replace) under the lock; a crash mid-save never leaves a torn scheduled_searches.json and no `.json.tmp` file is left behind after a successful save.
- `load_schedules()` never raises on missing/empty/corrupt data -- it returns [] and logs a warning, matching alerts.py's load_alerts behaviour.
- src/alerts.py and every other existing module are untouched; this slice adds exactly one new file.

## Must contain

- `DATA_DIR = Path('data')`
- `SCHEDULES_FILE = DATA_DIR / 'scheduled_searches.json'`
- `DEFAULT_INTERVAL_HOURS = 6.0`
- `def load_schedules() -> List[Dict]:`
- `def save_schedules(schedules: Dict[str, Dict]) -> None:`
- `def upsert_schedule(sched: Dict) -> None:`
- `def is_due(sched: Dict) -> bool:`
- `def effective_programs(sched: Dict) -> List[str]:`
- `def query_legs(sched: Dict) -> List[Dict]:`

## Scope

Only edit `src/scheduled_searches.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
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
