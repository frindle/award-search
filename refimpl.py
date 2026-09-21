#!/usr/bin/env python3
"""Reference impl for: aw-app-wiring-s5-app-include-router-sched

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Write the SIMPLEST change that makes the verify pass. It doubles as your review
reference when the model's diff comes back.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/app.py'
t = p.read_text()

OLD = """app = FastAPI(title="Award Search", lifespan=lifespan)"""
NEW = """app = FastAPI(title="Award Search", lifespan=lifespan)
app.include_router(scheduled_routes.router)"""

assert OLD in t, "refimpl anchor not found -- did the target change?"
assert "include_router" not in t, "router already included; nothing to do"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
