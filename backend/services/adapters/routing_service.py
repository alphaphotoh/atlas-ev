import json

from backend.core.config import ORS_API_KEY
from backend.core.http_client import HttpClient

from backend.models.route import Route
from backend.services.routing.segment_service import SegmentService
from backend.utils.route_utils import RouteUtils


class RoutingService:

    BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

    @staticmethod
    async def get_route(start, end):

        headers = {
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json"
        }

        body = {
            "coordinates": [
                start,
                end
            ]
        }

        response = await HttpClient.post(
            RoutingService.BASE_URL,
            headers=headers,
            json=body
        )

        data = response.json()

        ors_route = data["routes"][0]

        print("\n========== ORS ROUTE KEYS ==========")
        print(list(ors_route.keys()))

        print("\n========== ORS SEGMENTS ==========")
        print(json.dumps(
            ors_route.get("segments", []),
            indent=2
        )[:10000])

        geometry = RouteUtils.decode_route(
            ors_route["geometry"]
        )

        route = Route(

            encoded_geometry=ors_route["geometry"],

            geometry=geometry,

            distance_km=ors_route["summary"]["distance"] / 1000,

            duration_minutes=ors_route["summary"]["duration"] / 60,

            raw=ors_route

        )

        return SegmentService.build(route)