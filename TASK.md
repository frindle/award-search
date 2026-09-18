# TASK: aw-scheduled-searches-s2-date-ranges-start-2026-0

## Confirmed defect (observed, not suspected)

`src/scheduled_searches.py` is an empty stub -- it contains only a docstring and
no code. Verified by reading the file: there is no `build_query`, no
`normalize_date_ranges`, and nothing that produces the engine-ready query dict
with a normalised `date_ranges` list, so scheduled searches cannot be built at
all.

## Entry point

src/scheduled_searches.py:1 (the whole module must be created)

## Required change

In src/scheduled_searches.py: 'date_ranges':[{'start':'2026-03-01','end':'2026-03-15'}],.

Create the module with exactly this contract:

- `DEFAULT_QUERY` -- a dict of the default scheduled-search query:
  `"origin": "JFK"`, `"destination": "LAX"`, `"cabin": "business"`, and
  `'date_ranges':[{'start':'2026-03-01','end':'2026-03-15'}],` as the default
  date range.
- `normalize_date_ranges(search)` -- takes a dict `search` and returns the
  resolved `date_ranges` list, in this priority order:
  1. If `search["date_ranges"]` is a list containing at least one VALID entry,
     return exactly those valid entries (each as its own dict). An entry is
     valid iff it is a dict whose `"start"` and `"end"` are both non-empty
     strings; anything else (None, numbers, strings, dicts missing either key,
     empty-string values) is dropped.
  2. Else if `search` has string `"start"` AND `"end"`, return one range with
     the earlier date as `"start"` and the later as `"end"` (swap them when
     given out of order).
  3. Else if `search` has a string `"date"`, return a single-day range
     `[{"start": <date>, "end": <date>}]`.
  4. Otherwise fall back to the default ranges from `DEFAULT_QUERY`.
- `build_query(search=None)` -- merges `search` over `DEFAULT_QUERY` and sets
  `"date_ranges"` via `normalize_date_ranges`. Rules:
  - `None` or a non-dict `search` is treated as `{}` (must not raise).
  - Every key of `search` except `"start"`, `"end"`, `"date"` overrides the
    corresponding default.
  - The returned dict has exactly the keys `origin`, `destination`,
    `cabin`, `date_ranges` plus any extra override keys from `search`; it must
    never contain raw `start`/`end`/`date` keys, and it must not mutate or
    share mutable state with the input.

Behaviour that must NOT change:
- The default query (empty/None search) is exactly
  `{'origin': 'JFK', 'destination': 'LAX', 'cabin': 'business',
  'date_ranges': [{'start': '2026-03-01', 'end': '2026-03-15'}]}`.
- Invalid or degenerate inputs (None, non-dict entries in `date_ranges`,
  empty-string dates) are dropped silently -- they must never raise.

## Must contain

- `def build_query(search=None):`
- `def normalize_date_ranges(search):`
- `'date_ranges':[{'start':'2026-03-01','end':'2026-03-15'}],`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

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
