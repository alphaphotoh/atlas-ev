from typing import Literal

from pydantic import BaseModel


class TripRequest(BaseModel):
    vehicle: str = "vf9"

    origin: str

    destination: str

    waypoints: list[str] = []

    waypoint_mode: Literal[
        "required_stops",
        "via_points"
    ] = "required_stops"

    starting_soc: float

    average_speed: float = 110

    highway_ratio: float = 0.8