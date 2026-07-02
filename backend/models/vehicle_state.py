from dataclasses import dataclass


@dataclass
class VehicleState:

    speed_kmh: float

    temperature_c: float

    road_grade_percent: float

    wind_speed_kmh: float = 0

    hvac_kw: float = 0