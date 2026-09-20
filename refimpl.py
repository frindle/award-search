#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s6-seatsaeroclient-search-o

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Writes the complete solution into src/scheduled_runner.py from scratch.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src' / 'scheduled_runner.py'
p.parent.mkdir(parents=True, exist_ok=True)

SOLUTION = '''"""Scheduled runner: self-contained Seats.aero search client.

SeatsAeroClient.search(origin, destination, start_date, end_date, cabins,
programs) -> List[SeatsAeroAvailability]
"""
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

import requests


API_BASE = "https://seats.aero/partnerapi"

SOURCE_TO_PROGRAM = {
    "eurobonus": "sas",
    "virginatlantic": "virgin_atlantic",
    "aeromexico": "air_canada",
    "american": "american",
    "delta": "delta",
    "etihad": "etihad",
    "united": "united",
    "emirates": "emirates",
    "aeroplan": "air_canada",
    "alaska": "alaska",
    "velocity": "virgin_australia",
    "qantas": "qantas",
    "connectmiles": "copa",
    "azul": "azul",
    "smiles": "gol",
    "flyingblue": "flying_blue",
    "jetblue": "jetblue",
    "qatar": "qatar",
    "turkish": "turkish",
    "singapore": "singapore",
    "ethiopian": "ethiopian",
    "saudia": "saudia",
    "finnair": "finnair",
    "lufthansa": "lufthansa",
    "frontier": "frontier",
    "spirit": "spirit",
}

PROGRAM_TO_SOURCE = {v: k for k, v in SOURCE_TO_PROGRAM.items()}


@dataclass
class SeatsAeroAvailability:
    availability_id: str
    origin: str
    destination: str
    departure_date: Optional[date]
    source: str
    cabin_avail: Dict[str, bool]
    cabin_cost: Dict[str, int]
    cabin_seats: Dict[str, int]
    cabin_airlines: Dict[str, List[str]]
    cabin_direct: Dict[str, bool]


class SeatsAeroClient:
    def __init__(self, api_key: str = "test-key"):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"Partner-Authorization": self.api_key})

    def search(
        self,
        origin: str,
        destination: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        cabins: Optional[List[str]] = None,
        programs: Optional[List[str]] = None,
    ) -> List[SeatsAeroAvailability]:
        params = {
            "origin_airport": origin,
            "destination_airport": destination,
        }

        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        if cabins:
            params["cabins"] = ",".join(cabins)
        if programs:
            sources = [PROGRAM_TO_SOURCE[p] for p in programs if p in PROGRAM_TO_SOURCE]
            if sources:
                params["sources"] = ",".join(sources)

        try:
            response = self.session.get(f"{API_BASE}/search", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException:
            return []

        results = []
        for item in data.get("data", []):
            cabin_avail = {}
            cabin_cost = {}
            cabin_seats = {}
            cabin_airlines = {}
            cabin_direct = {}

            for cabin in ["economy", "premium", "business", "first"]:
                prefix = cabin.capitalize()
                cabin_avail[cabin] = bool(item.get(prefix + "Available", False))
                cost_val = item.get(prefix + "MileageCost")
                try:
                    cabin_cost[cabin] = int(str(cost_val).replace(",", "")) if cost_val else 0
                except (TypeError, ValueError):
                    cabin_cost[cabin] = 0
                cabin_seats[cabin] = int(item.get(prefix + "RemainingSeats", 0) or 0)
                cabin_airlines[cabin] = list(item.get(prefix + "Airlines", []) or [])
                cabin_direct[cabin] = bool(item.get(prefix + "Direct", False))

            departure_date = None
            if item.get("date"):
                try:
                    departure_date = date.fromisoformat(str(item["date"]))
                except ValueError:
                    departure_date = None

            results.append(SeatsAeroAvailability(
                availability_id=item.get("id", ""),
                origin=item.get("route", {}).get("originAirport", ""),
                destination=item.get("route", {}).get("destinationAirport", ""),
                departure_date=departure_date,
                source=item.get("source", ""),
                cabin_avail=cabin_avail,
                cabin_cost=cabin_cost,
                cabin_seats=cabin_seats,
                cabin_airlines=cabin_airlines,
                cabin_direct=cabin_direct,
            ))

        return results
'''

p.write_text(SOLUTION)
print("refimpl applied")
