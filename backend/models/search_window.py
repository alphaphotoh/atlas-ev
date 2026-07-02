from dataclasses import dataclass


@dataclass
class SearchWindow:

    start_segment: int

    end_segment: int

    start_distance_km: float

    end_distance_km: float