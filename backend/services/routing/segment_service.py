from backend.models.route_segment import RouteSegment
from backend.services.planning.corridor_service import CorridorService


class SegmentService:

    @staticmethod
    def build(route):

        segments = []

        cumulative_distance = 0

        geometry = route.geometry

        total_distance = route.distance_km

        total_duration = route.duration_minutes

        for i in range(len(geometry) - 1):

            start = geometry[i]

            end = geometry[i + 1]

            length = CorridorService.distance_km(
                start,
                end
            )

            cumulative_distance += length

            if total_distance > 0:

                duration = (
                    length /
                    total_distance
                ) * total_duration

            else:

                duration = 0

            center = [

                (start[0] + end[0]) / 2,

                (start[1] + end[1]) / 2

            ]

            segments.append(

                RouteSegment(

                    index=i,

                    start_coordinate=start,

                    end_coordinate=end,

                    center_coordinate=center,

                    length_km=length,

                    cumulative_distance_km=cumulative_distance,

                    duration_minutes=duration

                )

            )

        route.segments = segments

        return route