from backend.core.http_client import HttpClient


class ElevationService:
    API_URL = "https://api.open-meteo.com/v1/elevation"

    @staticmethod
    async def get_elevation(
        latitude,
        longitude,
    ):
        try:
            response = await HttpClient.get(
                ElevationService.API_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                },
            )

            data = response.json()

            elevation_values = data.get(
                "elevation",
                [],
            )

            if not elevation_values:
                return 0.0

            return float(
                elevation_values[0]
            )

        except Exception:
            return 0.0
