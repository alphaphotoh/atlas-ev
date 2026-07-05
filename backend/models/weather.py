from dataclasses import dataclass


@dataclass
class Weather:

    temperature_c: float

    wind_speed_kph: float

    wind_direction_degrees: float

    precipitation_mm: float

    snowfall_cm: float

    humidity_percent: float

    pressure_hpa: float