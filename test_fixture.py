"""Adversarial fixture for: aw-sched-routes-s5-everything-that-renders

Integration fixture: drives the real router through fastapi.testclient,
asserting status codes AND response bodies. The core property under test is
that EVERYTHING THAT RENDERS goes through TEMPLATES.TemplateResponse -- a fake
templates object records each TemplateResponse call (name + context) and
returns a plain Response whose body encodes the render, so an implementation
that returns plain dicts instead of rendered templates fails even when its
JSON payloads look right.

The target imports `..scheduled_runner` and `..transfer_partners`, which are
not part of this slice; the fixture registers fakes for them in sys.modules
BEFORE importing the target, so the import succeeds either way.
"""
import sys
import types
import importlib.util

# --- fake sibling modules (registered before exec) --------------------------
runner = types.ModuleType("src.scheduled_runner")
def run_schedule(program):
    return {"program": program, "status": "ok", "flights_found": 3}
runner.run_schedule = run_schedule

partners_mod = types.ModuleType("src.transfer_partners")
_PARTNERS = [
    {"code": "AA", "name": "American Airlines", "programs": ["AAdvantage"]},
    {"code": "DL", "name": "Delta Air Lines", "programs": ["SkyMiles"]},
]
partners_mod.list_partners = lambda: [dict(p) for p in _PARTNERS]

sys.modules.setdefault("src.scheduled_runner", runner)
sys.modules.setdefault("src.transfer_partners", partners_mod)

# The target uses relative imports (`from ..scheduled_runner import ...`), so it
# must be loaded under its real package name with parent packages registered.
import pathlib  # noqa: E402
_pkg_src = types.ModuleType("src")
_pkg_src.__path__ = [str(pathlib.Path("src").resolve())]
_pkg_webui = types.ModuleType("src.webui")
_pkg_webui.__path__ = [str(pathlib.Path("src/webui").resolve())]
sys.modules.setdefault("src", _pkg_src)
sys.modules["src.webui"] = _pkg_webui

spec = importlib.util.spec_from_file_location(
    "src.webui.scheduled_routes", 'src/webui/scheduled_routes.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC: a module loaded this way has no entry in sys.modules,
# so relative-import resolution and annotation lookups need it present.
sys.modules["src.webui.scheduled_routes"] = target
spec.loader.exec_module(target)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from starlette.responses import Response  # noqa: E402


class FakeTemplates:
    """Records every TemplateResponse call; renders a deterministic body."""
    def __init__(self):
        self.calls = []

    def TemplateResponse(self, name, context=None, **kwargs):
        import json as _json
        ctx = dict(context or {})
        self.calls.append((name, ctx))
        flat = ",".join(
            f"{k}={v if not isinstance(v, (dict, list)) else _json.dumps(v, sort_keys=True)}"
            for k, v in sorted(ctx.items())
        )
        return Response("RENDERED:" + name + ":" + flat, media_type="text/html")


fake = FakeTemplates()
target.init(fake)

app = FastAPI()
app.include_router(target.router)
client = TestClient(app)


def _rendered():
    return len(fake.calls) > 0 and all(c[0].endswith(".html") for c in fake.calls)


CASES = []

def add(desc, thunk):
    CASES.append((desc, thunk, True))


add("GET /api/scheduled/partners renders via TemplateResponse",
    lambda: client.get("/api/scheduled/partners").status_code == 200
            and client.get("/api/scheduled/partners").text.startswith("RENDERED:")
            and _rendered())

add("GET /api/scheduled/partners/aa (lowercase) renders with partner AA",
    lambda: client.get("/api/scheduled/partners/aa").status_code == 200
            and "American Airlines" in client.get("/api/scheduled/partners/aa").text)

add("GET /api/scheduled/partners/ZZZ -> 404 {'error': 'partner not found', 'code': 'ZZZ'}",
    lambda: client.get("/api/scheduled/partners/ZZZ").status_code == 404
            and client.get("/api/scheduled/partners/ZZZ").json()
            == {"detail": {"error": "partner not found", "code": "ZZZ"}})

add("POST /api/scheduled/run {} -> 422 invalid_program",
    lambda: client.post("/api/scheduled/run", json={}).status_code == 422
            and client.post("/api/scheduled/run", json={}).json()
            == {"detail": {"error": "program is required", "code": "invalid_program"}})

add("POST /api/scheduled/run {program} renders with the run payload",
    lambda: client.post("/api/scheduled/run", json={"program": "AAdvantage"}).status_code == 200
            and client.post("/api/scheduled/run", json={"program": "AAdvantage"}).text.startswith("RENDERED:")
            and _rendered())

add("GET /api/scheduled/templates renders via TemplateResponse",
    lambda: client.get("/api/scheduled/templates").status_code == 200
            and client.get("/api/scheduled/templates").text.startswith("RENDERED:")
            and _rendered())


def main():
    if len(CASES) < 3:
        print("  SCAFFOLD_INCOMPLETE: {} adversarial case(s) authored, need >= 3."
              .format(len(CASES)))
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
