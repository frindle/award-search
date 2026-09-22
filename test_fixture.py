"""Adversarial fixture for: aw-app-wiring-s4-scheduled-routes-init-te

The wiring under test: app.py must call `scheduled_routes.init(templates)`
exactly once, passing the SAME Jinja2Templates instance it uses itself. The
routes module is provided by a sibling slice and does not exist in this
worktree, so we register a recording stub as `src.webui.scheduled_routes`
BEFORE importing app -- then assert on what app.py actually passed to it.

Each case: (description, callable_returning_actual, expected)
"""
import sys
import types
from pathlib import Path

WT = Path(__file__).resolve().parent
sys.path.insert(0, str(WT))

# --- recording stub for the sibling-slice routes module ---------------------
_init_calls = []


def _stub_init(templates):
    _init_calls.append(templates)


_stub = types.ModuleType("src.webui.scheduled_routes")
_stub.init = _stub_init
sys.modules["src.webui.scheduled_routes"] = _stub

# --- import the real app as part of its package -----------------------------
import src.webui.app as target  # noqa: E402


CASES = [
    (
        "init() is called exactly once at import time",
        lambda: len(_init_calls),
        1,
    ),
    (
        "init() receives the SAME Jinja2Templates instance app.py uses",
        lambda: bool(_init_calls) and _init_calls[0] is target.templates,
        True,
    ),
    (
        "regression: GET / still renders 200 with the Award Search page",
        lambda: (lambda c: (r := c.get("/")).status_code == 200 and "Award Search" in r.text)(
            __import__("fastapi.testclient", fromlist=["TestClient"]).TestClient(target.app)
        ),
        True,
    ),
    (
        "unhappy path: GET /results/unknown-id -> 404 with the right detail",
        lambda: (lambda c: (r := c.get("/results/nope123")).status_code == 404 and r.json()["detail"] == "Search not found")(
            __import__("fastapi.testclient", fromlist=["TestClient"]).TestClient(target.app)
        ),
        True,
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
