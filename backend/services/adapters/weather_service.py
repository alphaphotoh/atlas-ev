from backend.models.weather import Weather

from backend.core.http_client import HttpClient


class WeatherService:

    BASE_URL = (
        "https://api.open-meteo.com/v1/forecast"
    )

    @staticmethod
    async def get_weather(
        latitude: float,
        longitude: float
    ) -> Weather:

        response = await HttpClient.get(

            WeatherService.BASE_URL,

            params={

                "latitude": latitude,

                "longitude": longitude,

                "current": ",".join([

                    "temperature_2m",

                    "wind_speed_10m",

                    "wind_direction_10m",

                    "relative_humidity_2m",

                    "pressure_msl",

                    "precipitation",

                    "snowfall"

                ])

            }

        )

        current = response.json()["current"]

        return Weather(

            temperature_c=current["temperature_2m"],

            wind_speed_kph=current["wind_speed_10m"],

            wind_direction_degrees=current["wind_direction_10m"],

            precipitation_mm=current["precipitation"],

            snowfall_cm=current["snowfall"],

            humidity_percent=current["relative_humidity_2m"],

            pressure_hpa=current["pressure_msl"]

        )