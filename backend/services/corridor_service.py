import math

from backend.services.charger_service import ChargerService
from backend.services.scoring_service import ScoringService
from backend.services.search_window_service import SearchWindowService
from backend.utils.async_utils import AsyncUtils


class CorridorService:

    DEFAULT_SPACING_KM = 25

    @staticmethod
    def distance_km(point1, point2):

        lat1, lon1 = point1[1], point1[0]
        lat2, lon2 = point2[1], point2[0]

        R = 6371

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        return R * c

    @staticmethod
    def sample_route(
        coordinates,
        spacing_km=None
    ):

        if spacing_km is None:
            spacing_km = CorridorService.DEFAULT_SPACING_KM

        if not coordinates:
            return []

        sampled = [coordinates[0]]

        accumulated = 0

        previous = coordinates[0]

        for point in coordinates[1:]:

            accumulated += CorridorService.distance_km(
                previous,
                point
            )

            if accumulated >= spacing_km:

                sampled.append(point)

                accumulated = 0

            previous = point

        if sampled[-1] != coordinates[-1]:
            sampled.append(coordinates[-1])

        return sampled

    @staticmethod
    async def search_point(point):

        for radius in (5, 10, 15):

            chargers = await ChargerService.search(
                latitude=point[1],
                longitude=point[0],
                distance_km=radius
            )

            if chargers:
                return chargers

        return []

    @staticmethod
    async def find_chargers_in_window(
        route,
        window
    ):

        search_points = SearchWindowService.search_points(
            route,
            window
        )

        print(
            f"Search points in window: {len(search_points)}"
        )

        tasks = [
            CorridorService.search_point(
                point["coordinate"]
            )
            for point in search_points
        ]

        search_results = await AsyncUtils.gather(tasks)

        unique_chargers = {}

        for chargers in search_results:

            for charger in chargers:

                charger_id = charger.id

                if charger.id is None:
                    continue

                if charger_id not in unique_chargers:

                    unique_chargers[charger_id] = (
                        ScoringService.score(charger)
                    )

        ranked = sorted(
            unique_chargers.values(),
            key=lambda charger: charger.score,
            reverse=True
        )

        print(
            f"Window chargers: {len(ranked)}"
        )

        return ranked