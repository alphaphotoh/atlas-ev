from dataclasses import dataclass


@dataclass
class RouteSegment:

    index: int

    start_coordinate: list[float]

    end_coordinate: list[float]

    center_coordinate: list[float]

    length_km: float

    cumulative_distance_km: float