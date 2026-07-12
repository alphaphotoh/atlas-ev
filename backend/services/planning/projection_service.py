from types import SimpleNamespace

from backend.models.projected_charger import ProjectedCharger
from backend.utils.geo_utils import GeoUtils


class ProjectionService:

    @staticmethod
    def project(
        route,
        charger
    ):
        segments = ProjectionService.get_segments(
            route
        )

        closest_distance = float("inf")
        projected_distance = 0.0

        for segment in segments:
            projection = ProjectionService.project_onto_segment(
                segment.start_coordinate,
                segment.end_coordinate,
                [
                    charger.longitude,
                    charger.latitude
                ]
            )

            distance = GeoUtils.distance_km(
                projection,
                [
                    charger.longitude,
                    charger.latitude
                ]
            )

            if distance >= closest_distance:
                continue

            closest_distance = distance

            segment_fraction = ProjectionService.segment_fraction(
                segment.start_coordinate,
                segment.end_coordinate,
                projection
            )

            projected_distance = (
                segment.cumulative_distance_km
                -
                segment.length_km
                +
                segment.length_km * segment_fraction
            )

        if closest_distance == float("inf"):
            closest_distance = 9999.0

        return ProjectedCharger(
            name=charger.name,
            network=charger.network,
            latitude=charger.latitude,
            longitude=charger.longitude,
            route_distance_km=projected_distance,
            detour_distance_km=closest_distance,
            power_kw=charger.power_kw,
            supports_vf9=charger.supports_vf9
        )

    @staticmethod
    def get_segments(route):
        route_segments = getattr(
            route,
            "segments",
            None
        )

        if route_segments:
            return route_segments

        geometry = getattr(
            route,
            "geometry",
            None
        ) or []

        segments = []
        cumulative_distance_km = 0.0

        for index in range(len(geometry) - 1):
            start = geometry[index]
            end = geometry[index + 1]

            length_km = GeoUtils.distance_km(
                start,
                end
            )

            if length_km <= 0:
                continue

            cumulative_distance_km += length_km

            segments.append(
                SimpleNamespace(
                    start_coordinate=start,
                    end_coordinate=end,
                    length_km=length_km,
                    cumulative_distance_km=cumulative_distance_km
                )
            )

        return segments

    @staticmethod
    def project_onto_segment(
        start,
        end,
        point
    ):
        ax, ay = start
        bx, by = end
        px, py = point

        abx = bx - ax
        aby = by - ay

        apx = px - ax
        apy = py - ay

        ab_squared = (
            abx * abx +
            aby * aby
        )

        if ab_squared == 0:
            return start

        t = (
            apx * abx +
            apy * aby
        ) / ab_squared

        t = max(
            0.0,
            min(1.0, t)
        )

        return [
            ax + abx * t,
            ay + aby * t
        ]

    @staticmethod
    def segment_fraction(
        start,
        end,
        projection
    ):
        total = GeoUtils.distance_km(
            start,
            end
        )

        if total == 0:
            return 0.0

        travelled = GeoUtils.distance_km(
            start,
            projection
        )

        return max(
            0.0,
            min(1.0, travelled / total)
        )