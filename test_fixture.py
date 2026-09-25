"""Adversarial fixture for: aw-sched-routes-s18-get-api-transfer-partner

INTEGRATION fixture: drives the real FastAPI router through TestClient and
asserts status codes AND response bodies. The target module uses relative
imports (`from ..transfer_partners import list_partners`) and two sibling
modules that do not exist in this worktree yet (src/transfer_partners.py,
src/scheduled_runner.py), so we register namespace packages + stub modules for
those siblings BEFORE loading the target -- exactly what a later slice will
provide. The route under test must return whatever `list_partners()` returns,
verbatim: a bare JSON array, not wrapped in an object.

Each case: (description, callable_returning_actual, expected)
"""
import importlib.util
import pathlib
import sys
import types

# --- stub the two sibling modules the target imports -----------------------
PARTNERS = [
    {"code": "AA", "name": "American Airlines"},
    {"code": "BA", "name": "British Airways"},
]

tp_mod = types.ModuleType("src.transfer_partners")
tp_mod.list_partners = lambda: [dict(p) for p in PARTNERS]
sys.modules["src.transfer_partners"] = tp_mod

sr_mod = types.ModuleType("src.scheduled_runner")
sr_mod.run_schedule = lambda program=None: {"ran": True, "program": program}
sys.modules["src.scheduled_runner"] = sr_mod

# --- namespace packages so relative imports resolve without executing src/__init__.py (which pulls in the CLI) ---
for _name in ("src", "src.webui"):
    if _name not in sys.modules:
        _pkg = types.ModuleType(_name)
        _pkg.__path__ = [str(pathlib.Path(_name))]
        sys.modules[_name] = _pkg

spec = importlib.util.spec_from_file_location(
    "src.webui.scheduled_routes", 'src/webui/scheduled_routes.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC so the module is resolvable by its own name.
sys.modules["src.webui.scheduled_routes"] = target
spec.loader.exec_module(target)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()
app.include_router(target.api_router)
client = TestClient(app)


def _get(path):
    resp = client.get(path)
    return (resp.status_code, resp.json())


# Model-drafted; NOT yet read by a human.
DRAFT_UNCONFIRMED = True

CASES = [
    ("GET /api/transfer-partners returns 200",
     lambda: _get("/api/transfer-partners")[0], 200),
    ("body is exactly list_partners() output -- bare array, not wrapped",
     lambda: _get("/api/transfer-partners")[1], PARTNERS),
    ("body is a JSON array of partner objects (not an object wrapper)",
     lambda: isinstance(_get("/api/transfer-partners")[1], list)
             and all(isinstance(p, dict) and "code" in p for p in _get("/api/transfer-partners")[1]),
     True),
    ("regression: GET /api/airport-groups still returns 200 with the real groups",
     lambda: _get("/api/airport-groups"), (200, target.list_groups())),
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
