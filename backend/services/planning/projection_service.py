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

        charger.nearest_segment = closest_segment.index
        charger.route_distance_km = (
            closest_segment.cumulative_distance_km
        )
        charger.detour_km = closest_distance

        return charger