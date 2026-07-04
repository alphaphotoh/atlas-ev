from dataclasses import dataclass

from backend.models.charging_candidate import ChargingCandidate


@dataclass
class SimulationResult:

    candidate: ChargingCandidate

    destination_soc: float

    requires_additional_stop: bool

    energy_used_kwh: float

    charging_time_minutes: float

    driving_time_minutes: float

    detour_time_minutes: float

    total_trip_time_minutes: float