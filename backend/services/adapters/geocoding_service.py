from backend.core.config import ORS_API_KEY
from backend.core.http_client import HttpClient


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

        response = await HttpClient.get(
            GeocodingService.BASE_URL,
            headers=headers,
            params=params
        )

        data = response.json()

        if not data.get("features"):

            raise Exception(
                f"Location not found: {location}"
            )

        return data