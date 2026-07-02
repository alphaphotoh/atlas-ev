from dataclasses import dataclass

from backend.models.charger import Charger


@dataclass
class ChargingPlan:

    charger: Charger

    arrival_soc: float

    target_soc: float

    charging_minutes: float

    total_trip_minutes: float