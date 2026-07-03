from dataclasses import dataclass


@dataclass
class TripPlanningConfig:

    preferred_arrival_soc: float = 10.0

    minimum_arrival_soc: float = 5.0

    maximum_departure_soc: float = 100.0

    safety_buffer_soc: float = 10.0

    road_trip_mode: bool = True