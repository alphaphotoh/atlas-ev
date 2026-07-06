from backend.models.trip_waypoint import (
    TripWaypoint,
)


class WaypointService:

    @staticmethod
    def build(
        origin: str,
        waypoints: list[str],
        destination: str
    ):

        stops = [

            origin,

            *waypoints,

            destination

        ]

        return [

            TripWaypoint(

                origin=stops[i],

                destination=stops[i + 1]

            )

            for i in range(

                len(stops) - 1

            )

        ]