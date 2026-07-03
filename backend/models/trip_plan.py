from dataclasses import dataclass, field

from backend.models.route import Route
from backend.models.battery_state import BatteryState


@dataclass
class TripPlan:

    route: Route

    battery_states: list[BatteryState] = field(default_factory=list)

    projected_chargers: list = field(default_factory=list)

    recommended_chargers: list = field(default_factory=list)

    metadata: dict = field(default_factory=dict)