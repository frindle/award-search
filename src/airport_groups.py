"""Airport code group expansion helpers."""
from typing import Iterable, List


def expand_codes(codes: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for code in codes:
        key = code.upper()
        if key not in seen:
            seen.add(key)
            result.append(key)
    return result
