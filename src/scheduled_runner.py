from .alert_filters import passes_filters
from .deeplinks import seats_aero_url
from .pushover import send_award_notification
from .seats_aero import SeatsAeroClient
from .scheduled_searches import effective_programs, is_due, load_schedules, query_legs, upsert_schedule


def select_results(alert, results):
    filters = alert.get("filters") or {}
    kept = []
    for r in results:
        try:
            if passes_filters(r, filters):
                kept.append(r)
        except Exception:
            continue
    return kept


def run_cycle(alerts, search_fn):
    out = {}
    for alert_id, alert in (alerts or {}).items():
        try:
            results = search_fn(alert or {})
        except Exception:
            continue
        kept = select_results(alert or {}, results)
        if kept:
            out[alert_id] = kept
    return out


def search_seats_aero(origin, destination, start_date=None, end_date=None, cabins=None, programs=None):
    client = SeatsAeroClient()
    return client.search(origin, destination, start_date, end_date, cabins, programs)
