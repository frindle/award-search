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


class _TripView:
    def __init__(self, total_taxes, taxes_currency, carriers):
        self.total_taxes = total_taxes
        self.taxes_currency = taxes_currency
        self.carriers = carriers


def get_trip(availability_id):
    try:
        client = SeatsAeroClient()
        trip = client.get_trip(availability_id)
    except Exception:
        return None
    if trip is None:
        return None
    return _TripView(float(trip.total_taxes) / 100.0, trip.taxes_currency, list(trip.carriers))
