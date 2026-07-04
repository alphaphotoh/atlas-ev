from backend.models.projected_charger import ProjectedCharger
from backend.utils.geo_utils import GeoUtils


class ProjectionService:

    @staticmethod
    def project(route, charger):

        closest_segment = None

        closest_distance = float("inf")

        for segment in route.segments:

            distance = GeoUtils.distance_km(

                segment.center_coordinate,

                [
                    charger.longitude,
                    charger.latitude
                ]

            )

            if distance < closest_distance:

                closest_distance = distance
                closest_segment = segment

        return ProjectedCharger(

            name=charger.name,

            network=charger.network,

            latitude=charger.latitude,

            longitude=charger.longitude,

            route_distance_km=closest_segment.cumulative_distance_km,

            detour_distance_km=closest_distance,

            power_kw=charger.power_kw,

            supports_vf9=charger.supports_vf9

        )