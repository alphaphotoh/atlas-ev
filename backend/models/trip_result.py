from dataclasses import dataclass

from backend.models.charging_candidate import ChargingCandidate


@dataclass
class TripResult:

    candidate: ChargingCandidate

    driving_time_minutes: float

    charging_time_minutes: float

    detour_time_minutes: float

    total_trip_time_minutes: float

    destination_soc: float