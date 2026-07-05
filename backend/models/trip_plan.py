from dataclasses import dataclass, field

from backend.models.vehicle import Vehicle
from backend.models.route import Route
from backend.models.trip_planning_config import TripPlanningConfig
from backend.models.simulation_context import SimulationContext
from backend.models.battery_state import BatteryState
from backend.models.charging_candidate import ChargingCandidate
from backend.models.simulation_result import SimulationResult
from backend.models.trip_leg import TripLeg
from backend.models.weather_sample import WeatherSample
from backend.models.efficiency_sample import EfficiencySample


@dataclass
class TripPlan:

    vehicle: Vehicle

    route: Route

    planning: TripPlanningConfig = field(
        default_factory=TripPlanningConfig
    )

    simulation: SimulationContext | None = None

    remaining_distance_km: float = 0.0

    starting_soc: float = 100.0

    battery_states: list[BatteryState] = field(
        default_factory=list
    )

    weather_samples: list[WeatherSample] = field(
        default_factory=list
    )

    efficiency_profile: list[EfficiencySample] = field(
        default_factory=list
    )

    corridor_chargers: list = field(
        default_factory=list
    )

    recommended_chargers: list[ChargingCandidate] = field(
        default_factory=list
    )

    results: list[SimulationResult] = field(
        default_factory=list
    )

    legs: list[TripLeg] = field(
        default_factory=list
    )

    def get_battery_state(
        self,
        distance_km: float
    ) -> BatteryState:

        return min(

            self.battery_states,

            key=lambda state: abs(

                state.distance_km -

                distance_km

            )

        )