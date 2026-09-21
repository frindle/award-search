#!/usr/bin/env python3
"""Reference impl for: aw-app-wiring-v2

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Adds to src/webui/app.py (preserving everything already there):
  1. `from ..webui.scheduled_routes import create_router, scheduled_search_loop`
     after the existing settings import;
  2. `scheduled_routes = create_router(templates)` + `app.include_router(scheduled_routes)`
     right after this app's Jinja2Templates instance is created;
  3. a second background task in lifespan:
     `scheduled_task = asyncio.create_task(scheduled_search_loop())`, cancelled on shutdown.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/app.py'
t = p.read_text()


def _insert_once(anchor: str, addition: str):
    global t
    if anchor in t and addition not in t:
        t = t.replace(anchor, anchor + "\n" + addition, 1)


# 1. import the router factory + background loop from the scheduled-search module
_insert_once(
    "from ..settings import load_settings, save_settings",
    "from ..webui.scheduled_routes import create_router, scheduled_search_loop",
)

# 2. build the APIRouter with this app's Jinja2Templates instance and mount it
_templates_line = 'templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "webui" / "templates"), autoescape=True)'
_insert_once(
    _templates_line,
    "scheduled_routes = create_router(templates)\napp.include_router(scheduled_routes)",
)

# 3. start the scheduled-search background loop alongside alert_scheduler
_insert_once(
    "    task = asyncio.create_task(alert_scheduler(_alert_search, _alert_notify, interval))",
    "    scheduled_task = asyncio.create_task(scheduled_search_loop())",
)
_insert_once(
    "    yield\n    task.cancel()",
    "    scheduled_task.cancel()",
)

p.write_text(t)
print("refimpl applied")
