import httpx

from backend.core.config import ORS_API_KEY
from backend.models.route import Route
from backend.services.segment_service import SegmentService
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

        async with httpx.AsyncClient() as client:
            response = await client.post(
                RoutingService.BASE_URL,
                headers=headers,
                json=body
            )

        response.raise_for_status()

        data = response.json()
        print("========== ORS RESPONSE ==========")
        print(data)
        print("==================================")



        ors_route = data["routes"][0]
        print("=== ORS ROUTE ===")
        print(type(ors_route["geometry"]))
        print(str(ors_route["geometry"])[:500])



        encoded_geometry = ors_route["geometry"]

        print(type(encoded_geometry))
        print(encoded_geometry)

        geometry = RouteUtils.decode_route(encoded_geometry)

        print(f"Decoded geometry points: {len(geometry)}")

        if geometry:
            print(f"First point: {geometry[0]}")
            print(f"Last point: {geometry[-1]}")

        route = Route(
            encoded_geometry=encoded_geometry,
            geometry=geometry,
            distance_km=ors_route["summary"]["distance"] / 1000,
            duration_minutes=ors_route["summary"]["duration"] / 60,
            raw=ors_route
        )

        route = SegmentService.build(route)

        print(f"Segments built: {len(route.segments)}")

        return route