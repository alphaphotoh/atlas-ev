import os

import httpx

from backend.models.route import Route


class RoutingService:
    ORS_ROUTE_URL = (
        "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    )

    TIMEOUT_SECONDS = 60

    @staticmethod
    async def get_route(
        start,
        end
    ):
        return await RoutingService.get_route_with_coordinates(
            coordinates=[
                start,
                end
            ]
        )

    @staticmethod
    async def get_route_with_coordinates(
        coordinates
    ):
        api_key = RoutingService.get_api_key()

        payload = {
            "coordinates": coordinates,
            "instructions": False,
            "geometry": True
        }

        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/geo+json, application/json"
        }

        async with httpx.AsyncClient(
            timeout=RoutingService.TIMEOUT_SECONDS
        ) as client:
            response = await client.post(
                RoutingService.ORS_ROUTE_URL,
                json=payload,
                headers=headers
            )

        if response.status_code >= 400:
            raise RuntimeError(
                "OpenRouteService route request failed. "
                f"Status: {response.status_code}. "
                f"Response: {response.text[:500]}"
            )

        data = response.json()

        return RoutingService.parse_geojson_route(
            data
        )

    @staticmethod
    async def get_route_via_waypoints(
        start,
        waypoint_coordinates,
        end
    ):
        coordinates = [
            start
        ]

        coordinates.extend(
            waypoint_coordinates
        )

        coordinates.append(
            end
        )

        return await RoutingService.get_route_with_coordinates(
            coordinates=coordinates
        )

    @staticmethod
    def parse_geojson_route(data):
        features = data.get(
            "features",
            []
        )

        if not features:
            raise RuntimeError(
                "OpenRouteService returned no route features."
            )

        feature = features[0]

        geometry = (
            feature.get(
                "geometry",
                {}
            ).get(
                "coordinates",
                []
            )
        )

        properties = feature.get(
            "properties",
            {}
        )

        summary = properties.get(
            "summary",
            {}
        )

        distance_meters = summary.get(
            "distance",
            0.0
        )

        duration_seconds = summary.get(
            "duration",
            0.0
        )

        distance_km = (
            float(distance_meters) /
            1000
        )

        duration_minutes = (
            float(duration_seconds) /
            60
        )

        return RoutingService.build_route(
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            geometry=geometry,
            raw=data
        )

    @staticmethod
    def build_route(
        distance_km,
        duration_minutes,
        geometry,
        raw
    ):
        return Route(
            distance_km=distance_km,
            geometry=geometry,
            encoded_geometry="",
            duration_minutes=duration_minutes,
            raw=raw
        )

    @staticmethod
    def get_api_key():
        possible_names = [
            "OPENROUTESERVICE_API_KEY",
            "ORS_API_KEY",
            "OPEN_ROUTE_SERVICE_API_KEY",
            "OPENROUTE_API_KEY"
        ]

        for name in possible_names:
            value = os.getenv(
                name
            )

            if value:
                return value

        raise RuntimeError(
            "OpenRouteService API key is missing. "
            "Set OPENROUTESERVICE_API_KEY or ORS_API_KEY in your .env file."
        )