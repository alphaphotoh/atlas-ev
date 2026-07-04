from dataclasses import dataclass

from backend.models.battery_state import BatteryState
from backend.models.projected_charger import ProjectedCharger


@dataclass
class ChargingCandidate:

    charger: ProjectedCharger

    battery_state: BatteryState

    arrival_soc: float

    departure_soc: float

    destination_arrival_soc: float

    charge_added_kwh: float

    charging_time_minutes: float

    total_trip_time_minutes: float

    score: float