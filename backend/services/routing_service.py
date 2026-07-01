import httpx

from backend.core.config import ORS_API_KEY


class RoutingService:

    BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

    @staticmethod
    async def get_route(origin, destination):

        headers = {
            "Authorization": ORS_API_KEY
        }

        params = {
            "start": origin,
            "end": destination
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                RoutingService.BASE_URL,
                headers=headers,
                params=params
            )

        return response.json()