import httpx

from backend.core.config import OPENCHARGEMAP_API_KEY
from backend.models.charger import Charger


class ChargerService:

    BASE_URL = "https://api.openchargemap.io/v3/poi"

    @staticmethod
    async def search(
        latitude: float,
        longitude: float,
        distance_km: float = 10
    ):

        params = {
            "key": OPENCHARGEMAP_API_KEY,
            "latitude": latitude,
            "longitude": longitude,
            "distance": distance_km,
            "distanceunit": "KM",
            "maxresults": 20
        }

        async with httpx.AsyncClient(http2=False) as client:

            response = await client.get(
                ChargerService.BASE_URL,
                params=params,
                timeout=30
            )

            response.raise_for_status()

            chargers = response.json()

        results = []

        for charger in chargers:

            address = charger.get("AddressInfo", {})
            connections = charger.get("Connections", [])
            operator = charger.get("OperatorInfo") or {}

            power_kw = None

            if connections:
                power_kw = connections[0].get("PowerKW")

            supported_connectors = []

            for connection in connections:

                connector = connection.get(
                    "ConnectionType",
                    {}
                ).get("Title")

                if connector:
                    supported_connectors.append(
                        connector
                    )

            supports_vf9 = any(
                "CCS" in connector or
                "J1772" in connector
                for connector in supported_connectors
            )

            if not supports_vf9:
                continue

            results.append(

                Charger(

                    id=charger.get("ID"),

                    name=address.get("Title"),

                    address=address.get("AddressLine1"),

                    latitude=address.get("Latitude"),

                    longitude=address.get("Longitude"),

                    distance_km=address.get("Distance"),

                    power_kw=power_kw,

                    network=operator.get("Title"),

                    connectors=supported_connectors,

                    num_connections=len(connections),

                    supports_vf9=supports_vf9

                )

            )

        results.sort(

            key=lambda charger: (

                -(charger.power_kw or 0),

                charger.distance_km or 9999

            )

        )

        return results