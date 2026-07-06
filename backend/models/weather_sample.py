from dataclasses import dataclass

from backend.models.environment_sample import (
    EnvironmentSample,
)
from backend.models.weather import Weather


@dataclass
class WeatherSample(EnvironmentSample):

    weather: Weather