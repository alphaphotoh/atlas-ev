from backend.models.route_segment import RouteSegment
from backend.services.corridor_service import CorridorService


class SegmentService:

    @staticmethod
    def build(route):

        segments = []

        cumulative = 0

        geometry = route.geometry

        for i in range(len(geometry) - 1):

            start = geometry[i]

            end = geometry[i + 1]

            length = CorridorService.distance_km(
                start,
                end
            )

            cumulative += length

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

                    cumulative_distance_km=cumulative

                )

            )

        route.segments = segments

        return route