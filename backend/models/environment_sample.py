from dataclasses import dataclass

from backend.models.weather import Weather


@dataclass
class EnvironmentSample:

    route_distance_km: float

    latitude: float

    longitude: float

    weather: Weather

    elevation_m: float | None = None

    grade_percent: float = 0.0