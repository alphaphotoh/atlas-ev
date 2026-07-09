import asyncio

from backend.core.http_client import HttpClient
from backend.models.weather import Weather


class WeatherService:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    DEFAULT_TEMPERATURE_C = 20.0
    DEFAULT_WIND_SPEED_KPH = 0.0
    DEFAULT_WIND_DIRECTION_DEGREES = 0.0
    DEFAULT_HUMIDITY_PERCENT = 50.0
    DEFAULT_PRESSURE_HPA = 1013.0
    DEFAULT_PRECIPITATION_MM = 0.0
    DEFAULT_SNOWFALL_CM = 0.0

    MAX_RETRIES = 2
    RETRY_DELAY_SECONDS = 0.5

    @staticmethod
    async def get_weather(latitude, longitude):
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(
                [
                    "temperature_2m",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "relative_humidity_2m",
                    "pressure_msl",
                    "precipitation",
                    "snowfall",
                ]
            ),
        }

        for attempt in range(WeatherService.MAX_RETRIES + 1):
            try:
                response = await HttpClient.get(
                    WeatherService.BASE_URL,
                    params=params,
                )

                data = response.json()
                current = data.get("current", {})

                return Weather(
                    temperature_c=WeatherService.safe_float(
                        current.get("temperature_2m"),
                        WeatherService.DEFAULT_TEMPERATURE_C,
                    ),
                    wind_speed_kph=WeatherService.safe_float(
                        current.get("wind_speed_10m"),
                        WeatherService.DEFAULT_WIND_SPEED_KPH,
                    ),
                    wind_direction_degrees=WeatherService.safe_float(
                        current.get("wind_direction_10m"),
                        WeatherService.DEFAULT_WIND_DIRECTION_DEGREES,
                    ),
                    humidity_percent=WeatherService.safe_float(
                        current.get("relative_humidity_2m"),
                        WeatherService.DEFAULT_HUMIDITY_PERCENT,
                    ),
                    pressure_hpa=WeatherService.safe_float(
                        current.get("pressure_msl"),
                        WeatherService.DEFAULT_PRESSURE_HPA,
                    ),
                    precipitation_mm=WeatherService.safe_float(
                        current.get("precipitation"),
                        WeatherService.DEFAULT_PRECIPITATION_MM,
                    ),
                    snowfall_cm=WeatherService.safe_float(
                        current.get("snowfall"),
                        WeatherService.DEFAULT_SNOWFALL_CM,
                    ),
                )

            except Exception as error:
                if attempt < WeatherService.MAX_RETRIES:
                    await asyncio.sleep(
                        WeatherService.RETRY_DELAY_SECONDS * (attempt + 1)
                    )
                    continue

                print()
                print("Weather service unavailable.")
                print("Using fallback weather values.")
                print(error)

                return WeatherService.default_weather()

    @staticmethod
    def default_weather():
        return Weather(
            temperature_c=WeatherService.DEFAULT_TEMPERATURE_C,
            wind_speed_kph=WeatherService.DEFAULT_WIND_SPEED_KPH,
            wind_direction_degrees=WeatherService.DEFAULT_WIND_DIRECTION_DEGREES,
            humidity_percent=WeatherService.DEFAULT_HUMIDITY_PERCENT,
            pressure_hpa=WeatherService.DEFAULT_PRESSURE_HPA,
            precipitation_mm=WeatherService.DEFAULT_PRECIPITATION_MM,
            snowfall_cm=WeatherService.DEFAULT_SNOWFALL_CM,
        )

    @staticmethod
    def safe_float(value, fallback):
        if value is None:
            return fallback

        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback