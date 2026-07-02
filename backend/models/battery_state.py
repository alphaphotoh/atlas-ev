from dataclasses import dataclass


@dataclass
class BatteryState:

    segment_index: int

    distance_km: float

    soc: float

    energy_used_kwh: float