#!/usr/bin/env python3
"""Reference impl for: aw-alert-filters-contract

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Replaces passes_filters() with the real three-constraint contract and fixes
describe_filters() so numeric caps render instead of raising TypeError.
normalize_airlines() and filter_results() are preserved untouched.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/alert_filters.py'
t = p.read_text()

OLD_PASSES = r'''def passes_filters(result: Dict, filters: Optional[Dict]) -> bool:
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
    return True'''

NEW_PASSES = r'''def _is_number(value) -> bool:
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
    return True'''

OLD_DESCRIBE = r'''def describe_filters(filters: Optional[Dict]) -> str:
    """Render a filter dict as a short human summary, e.g. 'airlines UA,NH'."""
    if not filters:
        return "(no filters)"
    parts = []
    for key, value in filters.items():
        codes = ",".join(normalize_airlines(value))
        parts.append("{} {}".format(key, codes) if codes else key)
    return "; ".join(parts)'''

NEW_DESCRIBE = r'''def describe_filters(filters: Optional[Dict]) -> str:
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
    return "; ".join(parts) if parts else "(no filters)"'''

assert OLD_PASSES in t, "refimpl anchor (passes_filters) not found -- did the target change?"
t = t.replace(OLD_PASSES, NEW_PASSES, 1)
assert OLD_DESCRIBE in t, "refimpl anchor (describe_filters) not found -- did the target change?"
t = t.replace(OLD_DESCRIBE, NEW_DESCRIBE, 1)

p.write_text(t)
print("refimpl applied")
