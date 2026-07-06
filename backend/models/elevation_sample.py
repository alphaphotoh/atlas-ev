from dataclasses import dataclass


@dataclass
class ElevationSample:

    distance_km: float

    elevation_m: float

    grade_percent: float