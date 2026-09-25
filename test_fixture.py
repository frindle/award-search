"""Adversarial fixture for: aw-sched-routes-s9-get-scheduled-new-templa

Integration fixture: drives the real router from src/webui/scheduled_routes.py
through a FastAPI TestClient and asserts status codes AND what the route asked
the template engine to render (template name + context). A benign implementation
(no /new route, wrong template, non-empty schedule, JSON instead of a template)
fails at least one case.

The sibling modules this slice chain has not landed yet (scheduled_runner,
transfer_partners) are stubbed in sys.modules BEFORE the target is loaded so
its relative imports resolve; that is environment setup, not part of what is
tested. The template engine is a recorder: it captures (name, context) and
returns a sentinel string, so we can assert exactly what the route passed.

Each case: (description, callable_returning_actual, expected)
"""
import importlib.util
import sys
import types
from pathlib import Path


def _stub(name, **attrs):
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


_stub("src", __path__=[])
_stub("src.webui", __path__=[])
_stub("src.scheduled_runner", run_schedule=lambda **kw: {"ok": True})
_stub("src.transfer_partners", list_partners=lambda: [])

# REGISTER BEFORE EXEC so relative imports and any sys.modules lookups resolve.
spec = importlib.util.spec_from_file_location(
    "src.webui.scheduled_routes",
    Path(__file__).resolve().parent / 'src/webui/scheduled_routes.py',
)
target = importlib.util.module_from_spec(spec)
sys.modules["src.webui.scheduled_routes"] = target
spec.loader.exec_module(target)

# --- template recorder: captures what the route asked to render -------------
RENDERED = []


class FakeTemplates:
    def TemplateResponse(self, name, context):
        RENDERED.append((name, dict(context)))
        return "HTML:" + name


target.init(FakeTemplates())

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()
app.include_router(target.router)
client = TestClient(app)

# The exact EMPTY schedule the contract pins down (normalize_schedule({})).
EMPTY_SCHEDULE = {
    "id": None,
    "name": "",
    "origins": [],
    "destinations": [],
    "date_ranges": [],
    "cabins": [],
    "programs": [],
    "transfer_partners": [],
    "filters": {"airlines": [], "max_points": None, "max_taxes": None},
    "interval_hours": 6,
    "notify_pushover": False,
    "enabled": True,
}


def _fresh():
    """Hit the route with a clean render log; return the response."""
    del RENDERED[:]
    return client.get("/api/scheduled/scheduled/new")


CASES = [
    ("GET /scheduled/new -> 200 and renders scheduled_edit.html",
     lambda: (_fresh().status_code, RENDERED[-1][0]),
     (200, "scheduled_edit.html")),

    ("context carries mode='new' plus the request object",
     lambda: ((lambda r: (r.status_code, RENDERED[-1][1]["mode"], "request" in RENDERED[-1][1]))(_fresh())),
     (200, "new", True)),

    ("schedule is EMPTY -- exactly normalize_schedule({})",
     lambda: (lambda r: RENDERED[-1][1]["schedule"] == EMPTY_SCHEDULE)(_fresh()),
     True),

    ("context programs and partners are empty lists (nothing pre-checked)",
     lambda: (lambda r: (RENDERED[-1][1].get("programs"), RENDERED[-1][1].get("partners")))(_fresh()),
     ([], [])),

    ("regression: existing /api/scheduled/partners still returns its JSON list",
     lambda: client.get("/api/scheduled/partners").json(),
     {"partners": []}),
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
