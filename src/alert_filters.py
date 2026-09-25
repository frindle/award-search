"""Normalize raw airline filter values into comparable uppercase IATA codes."""
from typing import Dict, Iterable, List, Optional


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


def _is_number(value) -> bool:
    """True for int/float values; anything else (None, str, list...) is not a number."""
    return isinstance(value, (int, float))


def passes_filters(result: Dict, filters: Optional[Dict]) -> bool:
    """Decide whether one award-availability result is worth alerting on.

    Three independent constraints, each applied only when set; every constraint
    that IS set must pass (AND). An unset/None/empty constraint imposes nothing,
    and unknown filter keys are ignored. Never raises -- returns a bool.

      * airlines: at least one of the result's carriers is in the allowlist
        (set intersection non-empty); a missing/None/empty carrier list fails
        when an allowlist is set (cannot prove the hit is on an allowed carrier).
      * max_points: inclusive cap on result['cost']; exactly equal passes; a
        missing/non-numeric cost fails closed.
      * max_taxes: inclusive cap on result['taxes']; exactly equal passes; a
        missing/non-numeric taxes value fails closed (lets the scheduled_runner
        two-pass design drop an unavailable get_trip).
    """
    if not filters:
        return True
    airlines = filters.get("airlines")
    if airlines is not None:
        try:
            allowed = normalize_airlines(airlines)
        except TypeError:
            return False
        if allowed:
            carriers = result.get("airlines") if isinstance(result, dict) else None
            codes = normalize_airlines(carriers) if carriers is not None else []
            if not set(codes) & set(allowed):
                return False
    max_points = filters.get("max_points")
    if max_points is not None:
        cost = result.get("cost") if isinstance(result, dict) else None
        if not _is_number(max_points) or not _is_number(cost) or cost > max_points:
            return False
    max_taxes = filters.get("max_taxes")
    if max_taxes is not None:
        taxes = result.get("taxes") if isinstance(result, dict) else None
        if not _is_number(max_taxes) or not _is_number(taxes) or taxes > max_taxes:
            return False
    return True


def filter_results(results: Iterable[Dict], filters: Optional[Dict]) -> List[Dict]:
    return [result for result in results if passes_filters(result, filters)]


def describe_filters(filters: Optional[Dict]) -> str:
    """Render a filter dict as a short human summary, e.g. 'airlines UA,NH; max_points 90000'."""
    if not filters:
        return "(no filters)"
    parts = []
    airlines = filters.get("airlines")
    if airlines is not None:
        codes = ",".join(normalize_airlines(airlines))
        parts.append("airlines {}".format(codes) if codes else "airlines")
    for key in ("max_points", "max_taxes"):
        value = filters.get(key)
        if value is not None:
            parts.append("{} {}".format(key, value))
    return "; ".join(parts) if parts else "(no filters)"
