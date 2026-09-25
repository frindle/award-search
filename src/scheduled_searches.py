import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Dict, List

logger = logging.getLogger(__name__)

DATA_DIR = Path('data')
SCHEDULES_FILE = DATA_DIR / 'scheduled_searches.json'
DEFAULT_INTERVAL_HOURS = 6.0

_lock = Lock()


def _load_raw() -> Dict[str, Dict]:
    try:
        data = json.loads(SCHEDULES_FILE.read_text())
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"scheduled_searches.json unreadable ({e}); starting empty"); return {}
    if not isinstance(data, dict):
        logger.warning("scheduled_searches.json is not an object; starting empty")
        return {}
    return data


def load_schedules() -> List[Dict]:
    return list(_load_raw().values())


def save_schedules(schedules: Dict[str, Dict]) -> None:
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True); tmp = SCHEDULES_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(schedules, indent=2))
        tmp.replace(SCHEDULES_FILE)


def upsert_schedule(sched: Dict) -> None:
    data = _load_raw()
    data[sched["id"]] = sched
    save_schedules(data)


def is_due(sched: Dict) -> bool:
    if not sched.get("enabled", True):
        return False
    try:
        checked_at = datetime.fromisoformat(sched.get("last_checked") or "")
    except (TypeError, ValueError):
        return True
    interval_hours = sched.get("interval_hours") or DEFAULT_INTERVAL_HOURS
    return datetime.now() - checked_at >= timedelta(hours=interval_hours)


def effective_programs(sched: Dict) -> List[str]:
    seen = set()
    return [p for p in (sched.get("programs") or []) if not (p in seen or seen.add(p))]


def query_legs(sched: Dict) -> List[Dict]:
    origins, destinations, date_ranges = sched.get("origins") or [], sched.get("destinations") or [], sched.get("date_ranges") or []
    if not (origins and destinations and date_ranges):
        return []
    legs = []
    for origin in origins:
        for destination in destinations:
            for r in date_ranges:
                legs.append({"origin": origin, "destination": destination,
                             "start_date": r.get("start") or r.get("start_date"),
                             "end_date": r.get("end") or r.get("end_date")})
    return legs
