#!/usr/bin/env python3
"""Reference impl for: aw-app-wiring-s4-scheduled-routes-init-te

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Write the SIMPLEST change that makes the verify pass. It doubles as your review
reference when the model's diff comes back.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/app.py'
t = p.read_text()

CALL = "scheduled_routes.init(templates)"
if CALL in t:
    print("refimpl already applied -- nothing to do")
    sys.exit(0)

OLD = """app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "webui" / "templates"), autoescape=True)
"""
NEW = OLD + "\nscheduled_routes.init(templates)\n"

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
