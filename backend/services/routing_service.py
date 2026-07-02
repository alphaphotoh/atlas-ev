import httpx

from backend.core.config import ORS_API_KEY
from backend.models.route import Route
from backend.services.corridor_service import CorridorService
from backend.services.segment_service import SegmentService


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

        async with httpx.AsyncClient() as client:

            response = await client.post(
                RoutingService.BASE_URL,
                headers=headers,
                json=body
            )

        response.raise_for_status()

        data = response.json()

        ors_route = data["routes"][0]

        encoded_geometry = ors_route["geometry"]

        route = Route(

            encoded_geometry=encoded_geometry,

            geometry=CorridorService.decode_route(
                encoded_geometry
            ),

            distance_km=ors_route["summary"]["distance"] / 1000,

            duration_minutes=ors_route["summary"]["duration"] / 60,

            raw=ors_route

        )

        return SegmentService.build(route)