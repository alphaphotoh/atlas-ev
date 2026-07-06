from backend.models.elevation_sample import (
    ElevationSample,
)


class ElevationProfileService:

    @staticmethod
    def build(
        route
    ):

        profile = []

        previous = None

        for coordinate in route.geometry:

            distance = coordinate[3]

            elevation = coordinate[2]

            grade = 0.0

            if previous is not None:

                distance_change = (

                    distance -

                    previous[3]

                ) / 1000

                elevation_change = (

                    elevation -

                    previous[2]

                )

                if distance_change > 0:

                    grade = (

                        elevation_change /

                        (distance_change * 1000)

                    ) * 100

            profile.append(

                ElevationSample(

                    distance_km=round(

                        distance / 1000,

                        3

                    ),

                    elevation_m=round(

                        elevation,

                        1

                    ),

                    grade_percent=round(

                        grade,

                        2

                    )

                )

            )

            previous = coordinate

        return profile