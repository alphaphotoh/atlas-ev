from backend.core.http_client import HttpClient


class ElevationService:

    @staticmethod
    async def get_elevation(
        latitude,
        longitude
    ):

        response = await HttpClient.get(

            "https://api.open-meteo.com/v1/elevation",

            params={

                "latitude": latitude,

                "longitude": longitude

            }

        )

        data = response.json()

        return data["elevation"][0]