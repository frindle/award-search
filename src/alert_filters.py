"""Normalize raw airline filter values into comparable uppercase IATA codes."""
from typing import Dict, List, Optional


def normalize_airlines(value) -> List[str]:
    """Coerce a list/tuple of codes, a single code string, or None to
    uppercase stripped IATA codes; [] if none.

    Non-string entries inside a list/tuple are skipped silently. Any other
    input type raises TypeError.
    """
    if value is None:
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, (list, tuple)):
        items = value
    else:
        raise TypeError("normalize_airlines expects a list, str or None")

    codes = []
    for entry in items:
        if not isinstance(entry, str):
            continue
        code = entry.strip().upper()
        if code:
            codes.append(code)
    return codes


def passes_filters(result: Dict, filters: Optional[Dict]) -> bool:
    """Return True when `result` satisfies every key in `filters`.

    A None or empty `filters` means "no filters" and always passes. Every
    filter key must be present in `result`; a missing key fails (never
    raises). Values are compared as lists of normalized IATA codes via
    normalize_airlines: case-insensitive, whitespace-stripped, order-sensitive.
    """
    if not filters:
        return True
    for key, wanted in filters.items():
        if key not in result:
            return False
        if normalize_airlines(result[key]) != normalize_airlines(wanted):
            return False
    return True
