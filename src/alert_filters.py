"""Normalize raw airline filter values into comparable uppercase IATA codes."""
from typing import List


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
