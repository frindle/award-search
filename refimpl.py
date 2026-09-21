#!/usr/bin/env python3
"""Reference impl for: aw-alert-filters-s4-filter-results

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

The target already contains normalize_airlines() and passes_filters() from an
earlier slice -- this ADDS filter_results() on top and preserves everything.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/alert_filters.py'
t = p.read_text()

if "def filter_results(" in t:
    print("refimpl already applied -- nothing to do")
    sys.exit(0)

# Extend the typing import with Iterable (needed by the new signature).
OLD_IMPORT = "from typing import Dict, List, Optional"
NEW_IMPORT = "from typing import Dict, Iterable, List, Optional"
assert OLD_IMPORT in t, "refimpl anchor not found -- did the target change?"
t = t.replace(OLD_IMPORT, NEW_IMPORT, 1)

# Append filter_results after passes_filters; keep every existing line.
APPEND = '''

def filter_results(results: Iterable[Dict], filters: Optional[Dict]) -> List[Dict]:
    """Return a new list of the results that pass `filters`, in original order.

    A None or empty `filters` means "no filters" and returns every result.
    Each result is tested with passes_filters (a missing filter key fails, it
    never raises). The input iterable is consumed once; the returned list is a
    fresh object sharing the same dict references -- results are not copied.
    """
    return [result for result in results if passes_filters(result, filters)]
'''
t = t.rstrip("\n") + "\n" + APPEND
p.write_text(t)
print("refimpl applied")
