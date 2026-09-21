DEFAULT_QUERY = {
    "origin": "JFK",
    "destination": "LAX",
    'date_ranges':[{'start':'2026-03-01','end':'2026-03-15'}],
    "cabin": "business",
}


def _valid_range(entry):
    return (isinstance(entry, dict)
            and isinstance(entry.get("start"), str)
            and entry.get("start")
            and isinstance(entry.get("end"), str)
            and entry.get("end"))


def normalize_date_ranges(search):
    ranges = search.get("date_ranges")
    if isinstance(ranges, list):
        valid = [dict(entry) for entry in ranges if _valid_range(entry)]
        if valid:
            return valid
    start, end = search.get("start"), search.get("end")
    if isinstance(start, str) and isinstance(end, str):
        lo, hi = (start, end) if start <= end else (end, start)
        return [{"start": lo, "end": hi}]
    date = search.get("date")
    if isinstance(date, str):
        return [{"start": date, "end": date}]
    return [dict(entry) for entry in DEFAULT_QUERY["date_ranges"]]


def build_query(search=None):
    search = dict(search) if isinstance(search, dict) else {}
    query = {key: value for key, value in DEFAULT_QUERY.items()}
    for key, value in search.items():
        if key not in ("start", "end", "date"):
            query[key] = value
    query["date_ranges"] = normalize_date_ranges(search)
    return query
