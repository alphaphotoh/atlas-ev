import httpx

from backend.core.config import ORS_API_KEY


class GeocodingService:

    BASE_URL = "https://api.openrouteservice.org/geocode/search"

    TIMEOUT = httpx.Timeout(
        connect=20.0,
        read=30.0,
        write=20.0,
        pool=20.0
    )

    @staticmethod
    async def search(location: str):

        headers = {
            "Authorization": ORS_API_KEY
        }

        params = {
            "text": location,
            "size": 1
        }

        print(f"Geocoding: {location}")

        async with httpx.AsyncClient(
            timeout=GeocodingService.TIMEOUT
        ) as client:

            response = await client.get(
                GeocodingService.BASE_URL,
                headers=headers,
                params=params
            )

        response.raise_for_status()

        data = response.json()

        if not data.get("features"):
            raise Exception(
                f"Location not found: {location}"
            )

        return data