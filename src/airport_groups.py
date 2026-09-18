"""Airport group codes -- city codes that fan out to several airports.

A *group* code (NYC, LON, PAR) stands for a set of member airports; a single
airport code (JFK, LAX) is never a group.
"""

GROUPS = {
    "NYC": ("JFK", "LGA", "EWR"),
    "LON": ("LHR", "STN", "LGW"),
    "PAR": ("CDG", "ORY"),
}


def is_group(code: str) -> bool:
    """Return True if `code` names a known airport group, else False.

    Matching is case-insensitive and ignores surrounding whitespace; non-string
    input (None, numbers) returns False instead of raising.
    """
    if not isinstance(code, str):
        return False
    return code.strip().upper() in GROUPS
