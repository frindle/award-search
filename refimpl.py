#!/usr/bin/env python3
"""Reference impl for: aw-app-wiring-s7-imported-as-from-schedul

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Three edits to src/webui/app.py:
  1. delete the local placeholder `async def schedule_scheduler` stub;
  2. add `from ..scheduled_runner import schedule_scheduler` at module scope;
  3. cancel sched_task after the yield in lifespan(), next to task.cancel().

Everything else in the file is preserved verbatim.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/app.py'
t = p.read_text()

# (2) import the real scheduler at module scope, right after the existing
#     webui-local imports.
OLD_IMPORT_ANCHOR = r"from . import scheduled_routes"
NEW_IMPORT_ANCHOR = r"""from . import scheduled_routes
from ..scheduled_runner import schedule_scheduler"""
assert OLD_IMPORT_ANCHOR in t, "refimpl anchor not found -- did the target change?"
t = t.replace(OLD_IMPORT_ANCHOR, NEW_IMPORT_ANCHOR, 1)

# (1) delete the local placeholder definition entirely.
OLD_PLACEHOLDER = r'''async def schedule_scheduler():
    """Placeholder for the scheduled-routes scheduler loop (later slice)."""
    return None


'''
assert OLD_PLACEHOLDER in t, "placeholder schedule_scheduler not found -- did the target change?"
t = t.replace(OLD_PLACEHOLDER, "", 1)

# (3) cancel sched_task on shutdown as well as task.
OLD_SHUTDOWN = r"""    yield
    task.cancel()
    logger.info("WebUI shutting down")"""
NEW_SHUTDOWN = r"""    yield
    task.cancel()
    sched_task.cancel()
    logger.info("WebUI shutting down")"""
assert OLD_SHUTDOWN in t, "lifespan shutdown block not found -- did the target change?"
t = t.replace(OLD_SHUTDOWN, NEW_SHUTDOWN, 1)

p.write_text(t)
print("refimpl applied")
