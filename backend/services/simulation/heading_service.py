import math


class HeadingService:

    @staticmethod
    def heading(
        point1,
        point2
    ):

        lon1 = math.radians(
            point1[0]
        )

        lat1 = math.radians(
            point1[1]
        )

        lon2 = math.radians(
            point2[0]
        )

        lat2 = math.radians(
            point2[1]
        )

        dlon = lon2 - lon1

        x = math.sin(dlon) * math.cos(lat2)

        y = (

            math.cos(lat1)

            * math.sin(lat2)

            -

            math.sin(lat1)

            * math.cos(lat2)

            * math.cos(dlon)

        )

        bearing = math.degrees(

            math.atan2(

                x,

                y

            )

        )

        return (

            bearing + 360

        ) % 360

    @staticmethod
    def heading_at_distance(
        route,
        distance_km
    ):

        if not route.segments:

            return 0

        segment = min(

            route.segments,

            key=lambda s: abs(

                s.cumulative_distance_km -

                distance_km

            )

        )

        index = segment.index

        if index >= len(route.geometry) - 1:

            index -= 1

        return HeadingService.heading(

            route.geometry[index],

            route.geometry[index + 1]

        )