# TASK: aw-sched-routes-s5-everything-that-renders

## Confirmed defect (observed, not suspected)

`src/webui/scheduled_routes.py` currently returns plain Python dicts from its
rendering routes (`/api/scheduled/templates`, `/api/scheduled/partners`,
`/api/scheduled/partners/{code}`, and the success path of
`/api/scheduled/run`). Verified by reading the file: each handler ends with a
bare `return {...}` (e.g. `return {"partners": list_partners()}`), so nothing
in this module ever calls `TEMPLATES.TemplateResponse`, even though
`init(templates)` stores a templates object in the module-level `TEMPLATES`.
The rest of the web UI (`src/webui/app.py`) renders exclusively via
`templates.TemplateResponse(...)`, so these routes are the odd ones out.

## Entry point

src/webui/scheduled_routes.py:27 (the first bare-dict return, in
`scheduled_templates`; the same pattern repeats at lines 32, 40 and 51)

## Required change

In src/webui/scheduled_routes.py: Everything that renders uses TEMPLATES.TemplateResponse.

Concretely: every route handler whose job is to RENDER a page (the
`/templates`, `/partners`, `/partners/{code}` GET routes and the success path
of `POST /run`) must return `TEMPLATES.TemplateResponse(...)` with an HTML
template name and a context dict that carries the data it used to return as a
plain dict. Handlers may take `request: Request` so the context can include
`{"request": request}` (required by modern Starlette TemplateResponse).

Behaviour that must NOT change:
- Route paths, methods, and the `/api/scheduled` prefix stay identical.
- `GET /partners/{code}` still matches case-insensitively and still raises
  HTTPException 404 with detail `{"error": "partner not found", "code": <code>}`
  for an unknown code (this path does NOT render).
- `POST /run` with a missing/empty program still raises HTTPException 422 with
  detail `{"error": "program is required", "code": "invalid_program"}`, and the
  success path still calls `run_schedule(program=body.program)` and surfaces its
  result in the rendered context.
- The module-level `init(templates)` hook and the `TEMPLATES` global keep their
  names; `RunRequest` keeps its shape (`program: str | None = None`).

## Must contain

- `TEMPLATES.TemplateResponse(`
- `def scheduled_templates(request: Request):`
- `def scheduled_partners(request: Request):`
- `def scheduled_partner(request: Request, code: str):`
- `def scheduled_run(request: Request, body: RunRequest):`
- `"partner not found"`
- `"program is required"`

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
