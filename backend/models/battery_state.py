from dataclasses import dataclass


@dataclass
class BatteryState:

    segment_index: int

    distance_km: float

    soc: float

    energy_used_kwh: float

    remaining_energy_kwh: float

    efficiency_kwh_per_100km: float

    speed_kmh: float

    elapsed_time_minutes: float