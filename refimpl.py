#!/usr/bin/env python3
"""Reference impl for: aw-scheduled-searches-store

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

The target currently holds only a one-line stub docstring; this writer replaces
it with the full module. The block below is RAW so any backslash in the source
stays literal.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/scheduled_searches.py'
p.parent.mkdir(parents=True, exist_ok=True)

NEW = r'''"""Persistent scheduled-search store + due/leg helpers.

Mirrors src/alerts.py: a json file under data/ keyed by schedule id, a
threading.Lock around writes, and an atomic tmp-write + Path.replace so a
crash mid-save never leaves a torn file. The runner (src/scheduled_runner.py)
imports effective_programs / is_due / load_schedules / query_legs /
upsert_schedule from here at module scope.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Dict, List

import logging

logger = logging.getLogger(__name__)

DATA_DIR = Path('data')
SCHEDULES_FILE = DATA_DIR / 'scheduled_searches.json'
DEFAULT_INTERVAL_HOURS = 6.0

_lock = Lock()


def load_schedules() -> List[Dict]:
    """Stored schedule records as a LIST (the runner iterates it directly).

    The on-disk shape is a dict keyed by schedule id, like alerts.json; this
    returns list(data.values()). Missing/empty/unreadable file -> [] with a
    warning, never an exception.
    """
    if not SCHEDULES_FILE.exists():
        return []
    try:
        data = json.loads(SCHEDULES_FILE.read_text())
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"scheduled_searches.json unreadable ({e}); starting empty")
        return []
    if not isinstance(data, dict):
        logger.warning("scheduled_searches.json is not an object; starting empty")
        return []
    return list(data.values())


def save_schedules(schedules: Dict[str, Dict]) -> None:
    """Atomic write under the lock: .json.tmp sibling, then Path.replace."""
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = SCHEDULES_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(schedules, indent=2))
        tmp.replace(SCHEDULES_FILE)


def upsert_schedule(sched: Dict) -> None:
    """Insert when new, replace in place when the id already exists."""
    data = {}
    if SCHEDULES_FILE.exists():
        try:
            raw = json.loads(SCHEDULES_FILE.read_text())
            if isinstance(raw, dict):
                data = raw
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"scheduled_searches.json unreadable ({e}); starting empty")
    data[sched['id']] = sched
    save_schedules(data)


def is_due(sched: Dict) -> bool:
    """True when the schedule should run now.

    Disabled records (enabled falsy; absent key counts as enabled) are never
    due. A missing/None/unparseable last_checked means "never checked" -> due.
    Otherwise due once at least interval_hours (default DEFAULT_INTERVAL_HOURS)
    have elapsed since the last check.
    """
    if not sched.get('enabled', True):
        return False
    last = sched.get('last_checked')
    if last is None:
        return True
    try:
        checked_at = datetime.fromisoformat(last)
    except (TypeError, ValueError):
        logger.warning(f"schedule {sched.get('id')} has unparseable last_checked; treating as due")
        return True
    interval_hours = sched.get('interval_hours') or DEFAULT_INTERVAL_HOURS
    return datetime.now() - checked_at >= timedelta(hours=interval_hours)


def effective_programs(sched: Dict) -> List[str]:
    """The schedule's own programs, deduplicated with original order kept."""
    programs = sched.get('programs') or []
    seen = set()
    out = []
    for p in programs:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def query_legs(sched: Dict) -> List[Dict]:
    """One leg per (origin, destination, date_range) combination.

    Each range is a dict with 'start'/'end' or 'start_date'/'end_date'.
    [] when any of the three inputs is missing or empty.
    """
    origins = sched.get('origins') or []
    destinations = sched.get('destinations') or []
    date_ranges = sched.get('date_ranges') or []
    if not origins or not destinations or not date_ranges:
        return []
    legs = []
    for origin in origins:
        for destination in destinations:
            for rng in date_ranges:
                legs.append({
                    'origin': origin,
                    'destination': destination,
                    'start_date': rng.get('start') or rng.get('start_date'),
                    'end_date': rng.get('end') or rng.get('end_date'),
                })
    return legs
'''

p.write_text(NEW)
print("refimpl applied")
