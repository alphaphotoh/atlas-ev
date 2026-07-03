from dataclasses import dataclass, field

from backend.models.vehicle import Vehicle
from backend.models.route import Route
from backend.models.battery_state import BatteryState
from backend.models.trip_planning_config import TripPlanningConfig


@dataclass
class TripPlan:

    vehicle: Vehicle

    route: Route

    planning: TripPlanningConfig = field(
        default_factory=TripPlanningConfig
    )

    battery_states: list[BatteryState] = field(
        default_factory=list
    )

    projected_chargers: list = field(
        default_factory=list
    )

    recommended_chargers: list = field(
        default_factory=list
    )

    results: list = field(
        default_factory=list
    )

    metadata: dict = field(
        default_factory=dict
    )