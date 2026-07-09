from dataclasses import dataclass, field

from backend.models.trip_plan import TripPlan


@dataclass
class Journey:
    trips: list[TripPlan] = field(default_factory=list)
    itineraries: list = field(default_factory=list)
    planning_results: list = field(default_factory=list)

    total_distance_km: float = 0.0
    total_duration_minutes: float = 0.0
    total_energy_kwh: float = 0.0

    total_driving_minutes: float = 0.0
    total_charging_minutes: float = 0.0
    total_detour_minutes: float = 0.0
    total_trip_minutes: float = 0.0

    total_stops: int = 0
    arrival_soc: float = 0.0