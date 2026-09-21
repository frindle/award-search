"""Adversarial fixture for: aw-app-wiring-s3-from-import-scheduled-ro

Integration fixture: drives the real FastAPI app through TestClient and
asserts status codes AND response bodies. The baseline (app.py without
`from . import scheduled_routes`) fails every /api/scheduled case with 404;
a correct wiring passes all of them while the regression cases keep holding.

Each case: (description, callable_returning_actual, expected)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient  # noqa: E402
from src.webui.app import app  # noqa: E402

client = TestClient(app)


CASES = [
    ("GET /api/scheduled/partners is wired (not 404)",
     lambda: client.get("/api/scheduled/partners").status_code, 200),
    ("partners list contains the AA partner",
     lambda: any(p["code"] == "AA" for p in client.get("/api/scheduled/partners").json()["partners"]), True),
    ("partner lookup is case-insensitive and returns the full record",
     lambda: client.get("/api/scheduled/partners/aa").json(), {"code": "AA", "name": "American Airlines"}),
    ("unknown partner code -> 404 with the error shape, not a 500",
     lambda: (client.get("/api/scheduled/partners/ZZ").status_code,
              client.get("/api/scheduled/partners/ZZ").json()["detail"]),
     (404, {"error": "partner not found", "code": "ZZ"})),
    ("regression: GET / still serves the home page",
     lambda: client.get("/").status_code, 200),
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
