from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TripWaypoint:

    origin: str

    destination: str

    trip: "TripPlan | None" = None