"""Airport code group expansion helpers."""
from typing import Dict, Iterable, List

AIRPORT_GROUPS: Dict[str, dict] = {
    "JFK": {"name": "New York (JFK)"},
    "LHR": {"name": "London (LHR)"},
}


def expand_codes(codes: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for code in codes:
        key = code.upper()
        if key not in seen:
            seen.add(key)
            result.append(key)
    return result


def group_label(code: str) -> str:
    return AIRPORT_GROUPS[code]['name'] if code in AIRPORT_GROUPS else code


def list_groups() -> List[Dict]:
    return [
        {"code": code, "name": AIRPORT_GROUPS[code]["name"], "airports": [code]}
        for code in sorted(AIRPORT_GROUPS)
    ]
