from backend.models.projected_charger import ProjectedCharger
from backend.utils.geo_utils import GeoUtils


class ProjectionService:

    @staticmethod
    def project(
        route,
        charger
    ):

        closest_segment = None

        closest_distance = float("inf")

        projected_distance = 0.0

        for segment in route.segments:

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

            closest_segment = segment

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