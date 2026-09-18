"""Adversarial fixture for: aw-sched-routes-s2-from-transfer-partners-i

INTEGRATION fixture: boots the real route module under uvicorn on a local port
and drives it over HTTP, asserting status codes AND response bodies. The CASES
list + main() runner below is unchanged from the scaffold; each case's thunk
returns (status_code, json_body) so the harness' equality check asserts both
halves of the contract.

Environment-robust on purpose: this file itself uses ONLY the stdlib (the
verify may run it under a bare venv python), and the uvicorn server is spawned
with whichever candidate interpreter actually has fastapi+uvicorn installed.

Cases separate "did the job" from "made the test go green":
  * exact body of GET /api/scheduled/partners (all three partners, sorted by
    code) -- an empty or unsorted list_partners() fails this
  * case-insensitive partner lookup (ua -> UA) -- a case-sensitive match fails
  * unknown code -> the RIGHT 404 with the error shape, not a 500
"""
import json
import pathlib
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# Load the target as src.webui.scheduled_routes WITHOUT executing src/__init__
# (which drags in the CLI and its heavy deps): register bare parent packages,
# then exec the file under its real dotted name so `from ..transfer_partners`
# resolves. This is exactly what a package import would do for this module.
SERVER_CODE = '''
import importlib.util, pathlib, sys, types

root = pathlib.Path(r"%ROOT%")
src_pkg = types.ModuleType("src"); src_pkg.__path__ = [str(root / "src")]
webui_pkg = types.ModuleType("src.webui"); webui_pkg.__path__ = [str(root / "src" / "webui")]
sys.modules["src"] = src_pkg
sys.modules["src.webui"] = webui_pkg

spec = importlib.util.spec_from_file_location(
    "src.webui.scheduled_routes", str(root / "src" / "webui" / "scheduled_routes.py"))
target = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = target
spec.loader.exec_module(target)

from fastapi import FastAPI
import uvicorn

app = FastAPI()
app.include_router(target.router)
uvicorn.run(app, host="127.0.0.1", port=%PORT%, log_level="error")
'''


def _pick_server_python():
    cands = [sys.executable, "python3", "/usr/local/bin/python3",
             "/opt/homebrew/bin/python3"]
    seen = set()
    for cand in cands:
        if not cand or cand in seen:
            continue
        seen.add(cand)
        r = subprocess.run([cand, "-c", "import fastapi, uvicorn"],
                           capture_output=True)
        if r.returncode == 0:
            return cand
    raise RuntimeError("no interpreter with fastapi+uvicorn found")


def _start_server():
    port = _free_port()
    code = (SERVER_CODE.replace("%ROOT%", str(ROOT))
                      .replace("%PORT%", str(port)))
    py = _pick_server_python()
    proc = subprocess.Popen(
        [py, "-c", code],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    base = "http://127.0.0.1:%d" % port
    deadline = time.time() + 25
    last_err = None
    while time.time() < deadline:
        if proc.poll() is not None:
            out = proc.stdout.read() if proc.stdout else ""
            raise RuntimeError("server exited early:\n" + out[-800:])
        try:
            with urllib.request.urlopen(base + "/api/scheduled/partners",
                                        timeout=1) as r:
                r.read()
            return base, proc  # any HTTP response means the server is up
        except Exception as e:
            last_err = e
            time.sleep(0.25)
    proc.terminate()
    raise RuntimeError("server never came up: %r" % (last_err,))


def _get(base, path):
    try:
        with urllib.request.urlopen(base + path, timeout=5) as r:
            status = r.status
            raw = r.read()
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read()
    body = json.loads(raw.decode("utf-8")) if raw else None
    return (status, body)


BASE = None  # set in __main__ before main() runs

CASES = [
    ("GET /api/scheduled/partners -> 200 with all partners sorted by code",
     lambda: _get(BASE, "/api/scheduled/partners"),
     (200, {"partners": [
         {"code": "AA", "name": "AAdvantage"},
         {"code": "DL", "name": "Delta SkyMiles"},
         {"code": "UA", "name": "United MileagePlus"}]})),
    ("GET /api/scheduled/partners/ua -> 200, case-insensitive lookup",
     lambda: _get(BASE, "/api/scheduled/partners/ua"),
     (200, {"code": "UA", "name": "United MileagePlus"})),
    ("GET /api/scheduled/partners/AA -> 200 exact-case hit",
     lambda: _get(BASE, "/api/scheduled/partners/AA"),
     (200, {"code": "AA", "name": "AAdvantage"})),
    ("unknown partner -> 404 with the error shape, not a 500",
     lambda: _get(BASE, "/api/scheduled/partners/ZZ"),
     (404, {"detail": {"error": "partner not found", "code": "ZZ"}})),
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
    base, proc = _start_server()
    BASE = base
    try:
        sys.exit(main())
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
