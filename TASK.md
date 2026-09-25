# TASK: aw-sched-routes-s7-parse-date-ranges

## Confirmed defect (observed, not suspected)

`src/webui/scheduled_routes.py` has no `parse_date_ranges` helper. The scheduled-search UI renders each template's date ranges as `{% for r in s.date_ranges %}{{ r.start }} → {{ r.end }}` (see `src/webui/templates/scheduled.html:53`), and the form submits starts/ends as two parallel comma-separated lists, but there is no function that turns those two flat string lists into the list of `{"start": ..., "end": ...}` dicts the template consumes. Verified by reading the target file (it ends at `parse_csv`, added in slice s6) and grepping `src/` for `parse_date_ranges` / `date_range` -- no definition exists anywhere.

## Entry point

src/webui/scheduled_routes.py:57 (end of file, after `parse_csv`)

## Required change

In src/webui/scheduled_routes.py add:

```python
def parse_date_ranges(starts: List[str], ends: List[str]) -> List[Dict]:
```

Contract:
- Inputs are two parallel lists of date strings (YYYY-MM-DD), as submitted by the form. Entries may carry surrounding whitespace; blank/whitespace-only entries must be dropped, and surviving entries stripped.
- Return a list of dicts `{"start": <str>, "end": <str or None>}` in input order: each surviving start at index *i* is paired with the end at index *i*; when there is no such end (more starts than ends) `"end"` is `None`. Extra ends beyond the number of starts are ignored.
- Empty inputs yield `[]`; the function must not raise on blank, uneven, or empty lists.

Behaviour that must NOT change:
- Every existing symbol stays intact and working: `RunRequest`, `router` (all five routes `/templates`, `/page/{name}`, `/partners`, `/partners/{code}`, `/run`), `TEMPLATES`, `init(templates)`, and the s6 helper `parse_csv("a, b ,c") == ["a", "b", "c"]`.
- The module must still import cleanly (its sibling imports `..scheduled_runner.run_schedule` and `..transfer_partners.list_partners` are untouched).

## Must contain

- `def parse_date_ranges(starts: List[str], ends: List[str]) -> List[Dict]:`
- `"start": start, "end": end`

(The gate holds the reference impl against this list. If the verify goes green
while one of these is absent from the changed files, the verify does not
enforce the spec -- that is a benign verify, caught mechanically.)

## Scope

Only edit `src/webui/scheduled_routes.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
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
