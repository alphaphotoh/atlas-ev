from dataclasses import dataclass, field

from backend.models.route import Route
from backend.models.battery_state import BatteryState
from backend.models.charging_candidate import ChargingCandidate


@dataclass
class TripLeg:

    number: int

    route: Route

    battery_states: list[BatteryState] = field(
        default_factory=list
    )

    results: list[ChargingCandidate] = field(
        default_factory=list
    )

    selected_result: ChargingCandidate | None = None