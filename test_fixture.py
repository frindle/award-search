"""Adversarial fixture for: aw-sched-routes-s1-from-airport-groups-impo

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

This is an INTEGRATION fixture: it drives the real FastAPI router through
fastapi.testclient.TestClient and asserts status codes AND response bodies.
The sibling `transfer_partners` module does not exist in this slice's tree, so
it is stubbed in sys.modules BEFORE the target loads; `airport_groups` is NOT
stubbed -- it must come from disk (created by the reference impl), which is
exactly what makes the fixture fail at baseline.
"""
import sys
import pathlib
import importlib.util

# --- isolate the target: register fake parent packages so relative imports
# resolve against our stubs and never execute src/__init__.py (which drags in
# the CLI/search stack). transfer_partners is a sibling slice's module that is
# absent here, so provide it; airport_groups must be real.
import types

_src = types.ModuleType("src")
_src.__path__ = [str(pathlib.Path('src').resolve())]  # real dir: airport_groups.py must load from disk
_webui = types.ModuleType("src.webui")
_webui.__path__ = [str(pathlib.Path('src/webui').resolve())]
_tp = types.ModuleType("src.transfer_partners")
_tp.list_partners = lambda: [
    {"code": "AA", "name": "American Airlines"},
    {"code": "DL", "name": "Delta Air Lines"},
]
sys.modules["src"] = _src
sys.modules["src.webui"] = _webui
sys.modules["src.transfer_partners"] = _tp

# Load the target under its REAL package name so `from ..airport_groups import ...`
# resolves to src.airport_groups (on disk) instead of failing as a top-level module.
spec = importlib.util.spec_from_file_location("src.webui.scheduled_routes", 'src/webui/scheduled_routes.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["src.webui.scheduled_routes"] = target
spec.loader.exec_module(target)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()
app.include_router(target.router)
client = TestClient(app)


def _groups_list():
    r = client.get("/api/scheduled/groups")
    assert r.status_code == 200, "GET /groups -> %s" % r.status_code
    body = r.json()
    groups = body["groups"]
    assert isinstance(groups, list) and len(groups) >= 1, \
        "groups must be a non-empty list, got %r" % (body,)
    for g in groups:
        assert set(g.keys()) == {"name", "codes"}, \
            "each group needs name+codes, got %r" % (g,)
        assert isinstance(g["name"], str) and g["name"]
        assert isinstance(g["codes"], list) and len(g["codes"]) >= 1, \
            "expand_codes must yield codes for a known group: %r" % (g,)
    return body


def _group_lookup():
    groups = _groups_list()["groups"]
    name = groups[0]["name"]
    r = client.get("/api/scheduled/groups/" + name)
    assert r.status_code == 200, "GET /groups/%s -> %s" % (name, r.status_code)
    body = r.json()
    assert body["codes"] == groups[0]["codes"], \
        "lookup must return the same codes as the listing: %r vs %r" % (body, groups[0])
    # case-insensitive lookup of a known group
    r2 = client.get("/api/scheduled/groups/" + name.lower())
    assert r2.status_code == 200, "case-insensitive GET /groups/%s -> %s" % (name.lower(), r2.status_code)
    assert r2.json()["codes"] == groups[0]["codes"], \
        "lowercase lookup must expand to the same codes: %r" % (r2.json(),)
    return body


def _group_404():
    r = client.get("/api/scheduled/groups/zzz-not-a-group")
    assert r.status_code == 404, \
        "unknown group must be a 404, got %s" % r.status_code
    detail = r.json()["detail"]
    assert isinstance(detail, dict) and "error" in detail, \
        "404 body must carry an error detail, got %r" % (r.json(),)
    return r.status_code


def _partners_regression():
    r = client.get("/api/scheduled/partners")
    assert r.status_code == 200, "GET /partners -> %s" % r.status_code
    body = r.json()
    codes = [p["code"] for p in body["partners"]]
    assert codes == ["AA", "DL"], "partner listing regressed: %r" % (body,)
    return codes


def _partner_lookup_regression():
    r = client.get("/api/scheduled/partners/dl")  # case-insensitive, pre-existing behaviour
    assert r.status_code == 200, "GET /partners/dl -> %s" % r.status_code
    body = r.json()
    assert body["code"] == "DL" and body["name"] == "Delta Air Lines", \
        "partner lookup regressed: %r" % (body,)
    return body


def _partner_404_regression():
    r = client.get("/api/scheduled/partners/zz")
    assert r.status_code == 404, "unknown partner must stay a 404, got %s" % r.status_code
    detail = r.json()["detail"]
    assert isinstance(detail, dict) and "error" in detail, \
        "partner 404 body regressed: %r" % (r.json(),)
    return r.status_code


CASES = [
    ("GET /api/scheduled/groups lists groups with expanded codes", _groups_list, None),
    ("GET /api/scheduled/groups/{name} expands a known group (case-insensitive)", _group_lookup, None),
    ("unknown group -> 404 with an error detail, not a 500", _group_404, 404),
    ("regression: GET /api/scheduled/partners still lists partners", _partners_regression, ["AA", "DL"]),
    ("regression: case-insensitive partner lookup still works", _partner_lookup_regression, {"code": "DL", "name": "Delta Air Lines"}),
    ("regression: unknown partner still 404s with an error detail", _partner_404_regression, 404),
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
        if want is not None and got != want:
            print("  FAIL {} -- got {!r}, want {!r}".format(desc, got, want))
            fails += 1
    print("  {}/{} case(s) passed".format(len(CASES) - fails, len(CASES)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
