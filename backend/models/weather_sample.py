from dataclasses import dataclass

from backend.models.weather import Weather


@dataclass
class WeatherSample:

    route_distance_km: float

    latitude: float

    longitude: float

    weather: Weather