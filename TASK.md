# TASK: aw-app-wiring-s3-from-import-scheduled-ro

## Confirmed defect (observed, not suspected)

The scheduled-routes API is unreachable in the web UI: with the app running,
`GET /api/scheduled/partners` returns 404. Reproduced by starting the FastAPI
app and hitting the route -- it 404s because `src/webui/app.py` never imports
the `scheduled_routes` module, so its router is never registered on the app.

## Entry point

src/webui/app.py:118 (`app = FastAPI(...)`; the relative-import block above it
is where sibling modules are wired in).

## Required change

In src/webui/app.py: add `from . import scheduled_routes` to the import block,
after the existing relative imports (e.g. right after the `..deeplinks` /
`..settings` imports), so importing the module registers its router on the app.
If `src/webui/scheduled_routes.py` or its dependency `src/transfer_partners.py`
are missing from your tree, create them first with their canonical content --
the reference impl does exactly this and is your review reference.

Behaviour that must NOT change:
- GET / still returns 200 (home page HTML).
- The app imports cleanly (`python3 -c "import src.webui.app"` succeeds).
- Existing routes (/search, /alerts, /settings) keep working.

## Must contain

- `from . import scheduled_routes`

## Scope

Only edit `src/webui/app.py`; do not edit `verify.sh`, `test_fixture.py` or `TASK.md`.
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
