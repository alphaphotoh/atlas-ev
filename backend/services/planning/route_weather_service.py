from backend.models.environment_sample import (
    EnvironmentSample,
)

from backend.services.adapters.weather_service import (
    WeatherService,
)

from backend.services.adapters.elevation_service import (
    ElevationService,
)

from backend.services.routing.route_segment_service import (
    RouteSegmentService,
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
        points = RouteSegmentService.sample_points(
            route=route,
            spacing_km=RouteWeatherService.SAMPLE_SPACING_KM
        )

        if not points:
            return []

        weather_tasks = []
        elevation_tasks = []

        for point in points:
            weather_tasks.append(
                WeatherService.get_weather(
                    latitude=point["latitude"],
                    longitude=point["longitude"]
                )
            )

            elevation_tasks.append(
                ElevationService.get_elevation(
                    latitude=point["latitude"],
                    longitude=point["longitude"]
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

        for point, current_weather, elevation in zip(
            points,
            weather,
            elevations
        ):
            grade = 0.0

            if previous is not None:
                distance_change = (
                    point["distance_km"] -
                    previous["distance_km"]
                )

                if distance_change > 0:
                    grade = (
                        (
                            elevation -
                            previous["elevation_m"]
                        ) /
                        (
                            distance_change * 1000
                        )
                    ) * 100

            environment.append(
                EnvironmentSample(
                    route_distance_km=point["distance_km"],
                    latitude=point["latitude"],
                    longitude=point["longitude"],
                    weather=current_weather,
                    elevation_m=elevation,
                    grade_percent=grade
                )
            )

            previous = {
                "distance_km": point["distance_km"],
                "elevation_m": elevation
            }

        return environment