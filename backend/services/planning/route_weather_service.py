from backend.models.weather_sample import WeatherSample

from backend.services.adapters.weather_service import WeatherService
from backend.services.planning.corridor_service import (
    CorridorService,
)
from backend.utils.async_utils import AsyncUtils


class RouteWeatherService:

    @staticmethod
    async def sample(
        route,
        spacing_km=25
    ):

        points = CorridorService.sample_route(

            route.geometry,

            spacing_km

        )

        tasks = [

            WeatherService.get_weather(

                latitude=point[1],

                longitude=point[0]

            )

            for point in points

        ]

        weather = await AsyncUtils.gather(

            tasks

        )

        samples = []

        route_distance = 0.0

        previous = None

        for point, conditions in zip(

            points,

            weather

        ):

            if previous is not None:

                route_distance += (

                    CorridorService.distance_km(

                        previous,

                        point

                    )

                )

            samples.append(

                WeatherSample(

                    route_distance_km=round(

                        route_distance,

                        1

                    ),

                    latitude=point[1],

                    longitude=point[0],

                    weather=conditions

                )

            )

            previous = point

        return samples