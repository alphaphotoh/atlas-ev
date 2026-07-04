import openrouteservice.convert


class RouteUtils:

    @staticmethod
    def decode_route(encoded_geometry):

        return openrouteservice.convert.decode_polyline(
            encoded_geometry
        )["coordinates"]