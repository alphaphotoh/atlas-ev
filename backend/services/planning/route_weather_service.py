from backend.models.environment_sample import (
    EnvironmentSample,
)

from backend.services.adapters.weather_service import (
    WeatherService,
)

from backend.services.adapters.elevation_service import (
    ElevationService,
)

from backend.utils.async_utils import (
    AsyncUtils,
)


class RouteWeatherService:

    SAMPLE_SPACING_KM = 25

    @staticmethod
    async def sample(
        route
    ):

        samples = []

        weather_tasks = []

        elevation_tasks = []

        for segment in route.segments:

            if (

                segment.cumulative_distance_km %

                RouteWeatherService.SAMPLE_SPACING_KM

            ) > segment.length_km:

                continue

            latitude = segment.center_coordinate[1]

            longitude = segment.center_coordinate[0]

            weather_tasks.append(

                WeatherService.get_weather(

                    latitude=latitude,

                    longitude=longitude

                )

            )

            elevation_tasks.append(

                ElevationService.get_elevation(

                    latitude=latitude,

                    longitude=longitude

                )

            )

            samples.append(

                (

                    segment.cumulative_distance_km,

                    latitude,

                    longitude

                )

            )

        weather = await AsyncUtils.gather(

            weather_tasks

        )

        elevations = await AsyncUtils.gather(

            elevation_tasks

        )

        environment = []

        previous = None

        for (

            distance,

            latitude,

            longitude

        ), current_weather, elevation in zip(

            samples,

            weather,

            elevations

        ):

            grade = 0.0

            if previous is not None:

                distance_change = (

                    distance -

                    previous["distance"]

                )

                if distance_change > 0:

                    grade = (

                        (

                            elevation -

                            previous["elevation"]

                        )

                        /

                        (

                            distance_change * 1000

                        )

                    ) * 100

            environment.append(

                EnvironmentSample(

                    route_distance_km=distance,

                    latitude=latitude,

                    longitude=longitude,

                    weather=current_weather,

                    elevation_m=elevation,

                    grade_percent=grade

                )

            )

            previous = {

                "distance": distance,

                "elevation": elevation

            }

        return environment