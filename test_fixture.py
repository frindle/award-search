"""Adversarial fixture for: aw-sched-routes-s20-program-choices-a-module

>>> THE ONE THING THE GENERATOR CANNOT WRITE FOR YOU <<<

CASES is empty and the verify FAILS until you fill it in. That is deliberate.
A generator can emit a verify that DISCRIMINATES (fails at baseline, passes on
a fix). It cannot decide whether the verify is RELEVANT -- whether it tests the
property the task actually asked for. A benign case passes broken work.

Pick inputs that separate "did the job" from "made the test go green":
  * the exact boundary the defect is about, and one on each side of it
  * the degenerate inputs (missing key, None, empty, wrong type) that must NOT
    raise
  * at least one case that a plausible WRONG fix would fail
  * the regression half: things that already work and must keep working

Each case: (description, callable_returning_actual, expected)
"""
import sys
import types
import importlib.util
from pathlib import Path

WT = Path(__file__).resolve().parent
sys.path.insert(0, str(WT))

# Sibling-slice modules that scheduled_routes.py imports but which are not part
# of THIS slice: stub them so the target module can be imported in isolation.
for name, attrs in (
    ("src.scheduled_runner", {"run_schedule": lambda **kw: {"ok": True}}),
    ("src.transfer_partners", {"list_partners": lambda: []}),
):
    if name not in sys.modules:
        mod = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(mod, k, v)
        sys.modules[name] = mod

spec = importlib.util.spec_from_file_location("target", 'src/webui/scheduled_routes.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["target"] = target
# Give it package context so its relative imports resolve against src.*.
target.__package__ = "src.webui"
spec.loader.exec_module(target)


def _config_programs():
    import yaml
    data = yaml.safe_load((WT / "config" / "programs.yml").read_text())
    return [(p["id"], p.get("name")) for p in data["programs"]]


def _integration_templates_route():
    """Drive the real router through a client: status code AND body."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.include_router(target.router)
    app.include_router(target.api_router)
    with TestClient(app) as client:
        resp = client.get("/api/scheduled/templates")
        return (resp.status_code, resp.json())


# Model-drafted; NOT yet read by a human.
DRAFT_UNCONFIRMED = True

CASES = [
    ("PROGRAM_CHOICES is a non-empty list",
     lambda: isinstance(getattr(target, "PROGRAM_CHOICES", None), list) and len(target.PROGRAM_CHOICES) > 0,
     True),
    ("every entry is {'id','name'} with non-empty strings",
     lambda: all(
         set(c.keys()) == {"id", "name"}
         and isinstance(c["id"], str) and c["id"]
         and isinstance(c["name"], str) and c["name"]
         for c in target.PROGRAM_CHOICES),
     True),
    ("covers every program id from config/programs.yml (no stale/hardcoded subset)",
     lambda: {c["id"] for c in target.PROGRAM_CHOICES} == {pid for pid, _ in _config_programs()},
     True),
    ("names match the configured display names",
     lambda: {c["id"]: c["name"] for c in target.PROGRAM_CHOICES} == dict(_config_programs()),
     True),
    ("regression: /api/scheduled/templates still serves 200 with its body shape",
     _integration_templates_route,
     (200, {"templates": []})),
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
