PROGRAMS = {
    "citi_typ": {"name": "Citi ThankYou Points",
                 "transfers_to": ["flying_blue", "jetblue", "qantas", "qatar", "singapore",
                                  "turkish", "virgin_atlantic", "etihad", "emirates"]},
    "capital_one": {"name": "Capital One Miles",
                    "transfers_to": ["air_canada", "emirates", "etihad", "finnair", "flying_blue",
                                     "qantas", "singapore", "turkish", "virgin_atlantic", "qatar"]},
    "bilt": {"name": "Bilt Rewards",
             "transfers_to": ["air_canada", "american", "emirates", "flying_blue", "turkish",
                              "united", "virgin_atlantic", "alaska"]},
    "wells_fargo": {"name": "Wells Fargo Rewards",
                    "transfers_to": ["air_canada", "flying_blue", "virgin_atlantic"]},
}

from collections.abc import Iterable
from typing import Dict, List


def list_partners() -> List[Dict]:
    partners = [
        {"id": slug, "name": info["name"], "programs": info["transfers_to"]}
        for slug, info in PROGRAMS.items()
    ]
    return sorted(partners, key=lambda partner: partner["name"])


def programs_for_partners(partner_ids: Iterable[str]) -> List[str]:
    ids = set(partner_ids)
    names = [info["name"] for info in PROGRAMS.values() if set(info["transfers_to"]) & ids]
    return sorted(names)


def partners_for_program(program: str) -> List[str]:
    info = PROGRAMS.get(program)
    if info is None:
        return []
    return sorted(info['transfers_to'])
