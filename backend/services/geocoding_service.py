import httpx

from backend.core.config import ORS_API_KEY


class GeocodingService:

    BASE_URL = "https://api.openrouteservice.org/geocode/search"

    @staticmethod
    async def search(location: str):

        headers = {
            "Authorization": ORS_API_KEY
        }

        params = {
            "text": location,
            "size": 1
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                GeocodingService.BASE_URL,
                headers=headers,
                params=params
            )

        return response.json()