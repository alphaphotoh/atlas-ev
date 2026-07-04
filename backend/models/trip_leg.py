from dataclasses import dataclass, field

from backend.models.route import Route
from backend.models.battery_state import BatteryState
from backend.models.simulation_result import SimulationResult


@dataclass
class TripLeg:

    number: int

    route: Route

    battery_states: list[BatteryState] = field(
        default_factory=list
    )

    results: list[SimulationResult] = field(
        default_factory=list
    )

    selected_result: SimulationResult | None = None