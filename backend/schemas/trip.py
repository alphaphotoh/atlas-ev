from typing import Literal

from pydantic import BaseModel


class TripConditionsRequest(BaseModel):
    passengers: int | None = None
    cargo_weight_kg: float | None = None

    climate_control: str | None = None
    cabin_target_temp_c: float | None = None

    driving_style: str | None = None
    road_condition: str | None = None
    tire_condition: str | None = None
    roof_load: str | None = None

    battery_degradation_percent: float | None = None


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

    traffic_mode: Literal[
        "none",
        "estimated",
        "live"
    ] = "none"

    traffic_level: Literal[
        "light",
        "moderate",
        "heavy"
    ] | None = None

    trip_conditions: TripConditionsRequest | None = None