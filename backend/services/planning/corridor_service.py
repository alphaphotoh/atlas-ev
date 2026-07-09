import asyncio
import math

from backend.services.adapters.charger_service import ChargerService
from backend.services.planning.corridor_cache import CorridorCache
from backend.services.planning.search_window_service import SearchWindowService


class CorridorService:
    DEFAULT_SPACING_KM = 40
    SEARCH_RADIUS_KM = 30
    SEARCH_BATCH_SIZE = 4
    FALLBACK_MIN_POWER_KW = 50

    @staticmethod
    def distance_km(point1, point2):
        lat1 = point1[1]
        lon1 = point1[0]
        lat2 = point2[1]
        lon2 = point2[0]

        earth_radius_km = 6371

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

        return earth_radius_km * c

    @staticmethod
    def sample_route(coordinates, spacing_km=None):
        if spacing_km is None:
            spacing_km = CorridorService.DEFAULT_SPACING_KM

        if not coordinates:
            return []

        sampled = [coordinates[0]]
        accumulated_km = 0.0
        previous = coordinates[0]

        for point in coordinates[1:]:
            accumulated_km += CorridorService.distance_km(
                previous,
                point
            )

            if accumulated_km >= spacing_km:
                sampled.append(point)
                accumulated_km = 0.0

            previous = point

        if sampled[-1] != coordinates[-1]:
            sampled.append(coordinates[-1])

        return sampled

    @staticmethod
    async def search_point(point):
        try:
            chargers = await ChargerService.search(
                latitude=point[1],
                longitude=point[0],
                distance_km=CorridorService.SEARCH_RADIUS_KM
            )

            return chargers or []

        except Exception as error:
            print()
            print("Charger search failed")
            print(error)
            return []

    @staticmethod
    async def search_points(points):
        all_chargers = []

        if not points:
            return all_chargers

        total_batches = math.ceil(
            len(points) / CorridorService.SEARCH_BATCH_SIZE
        )

        for index in range(
            0,
            len(points),
            CorridorService.SEARCH_BATCH_SIZE
        ):
            batch = points[
                index:index + CorridorService.SEARCH_BATCH_SIZE
            ]

            batch_number = (
                index // CorridorService.SEARCH_BATCH_SIZE
            ) + 1

            print(
                f"Searching charger batch "
                f"{batch_number} of {total_batches}"
            )

            results = await asyncio.gather(
                *[
                    CorridorService.search_point(point)
                    for point in batch
                ]
            )

            for group in results:
                all_chargers.extend(group)

        return all_chargers

    @staticmethod
    def charger_key(charger):
        charger_id = getattr(charger, "id", None)

        if charger_id is not None:
            return charger_id

        return (
            round(charger.latitude, 6),
            round(charger.longitude, 6)
        )

    @staticmethod
    def filter_chargers(chargers, trip):
        print()
        print(f"Filtering {len(chargers)} chargers")

        strict = {}

        removed_no_location = 0
        removed_no_power = 0
        removed_low_power = 0
        removed_connector = 0

        minimum_power_kw = trip.planning.minimum_dc_power_kw

        for charger in chargers:
            latitude = getattr(charger, "latitude", None)
            longitude = getattr(charger, "longitude", None)
            power_kw = getattr(charger, "power_kw", None)
            supports_vf9 = getattr(charger, "supports_vf9", False)

            if latitude is None or longitude is None:
                removed_no_location += 1
                continue

            if power_kw is None:
                removed_no_power += 1
                continue

            if power_kw < minimum_power_kw:
                removed_low_power += 1
                continue

            if not supports_vf9:
                removed_connector += 1
                continue

            strict[
                CorridorService.charger_key(charger)
            ] = charger

        print(f"No location: {removed_no_location}")
        print(f"No power: {removed_no_power}")
        print(f"Below {minimum_power_kw} kW: {removed_low_power}")
        print(f"Unsupported connector: {removed_connector}")
        print(f"Remaining after strict filter: {len(strict)}")

        if strict:
            return list(strict.values())

        print()
        print("No chargers passed strict filter.")
        print(
            f"Trying fallback filter with "
            f"{CorridorService.FALLBACK_MIN_POWER_KW} kW minimum."
        )

        fallback = {}

        fallback_no_location = 0
        fallback_no_power = 0
        fallback_low_power = 0
        fallback_connector = 0

        for charger in chargers:
            latitude = getattr(charger, "latitude", None)
            longitude = getattr(charger, "longitude", None)
            power_kw = getattr(charger, "power_kw", None)
            supports_vf9 = getattr(charger, "supports_vf9", False)

            if latitude is None or longitude is None:
                fallback_no_location += 1
                continue

            if power_kw is None:
                fallback_no_power += 1
                continue

            if power_kw < CorridorService.FALLBACK_MIN_POWER_KW:
                fallback_low_power += 1
                continue

            if not supports_vf9:
                fallback_connector += 1
                continue

            fallback[
                CorridorService.charger_key(charger)
            ] = charger

        print(f"Fallback no location: {fallback_no_location}")
        print(f"Fallback no power: {fallback_no_power}")
        print(
            f"Fallback below "
            f"{CorridorService.FALLBACK_MIN_POWER_KW} kW: "
            f"{fallback_low_power}"
        )
        print(f"Fallback unsupported connector: {fallback_connector}")
        print(f"Remaining after fallback filter: {len(fallback)}")

        return list(fallback.values())

    @staticmethod
    async def find_chargers(trip):
        cached = CorridorCache.get(trip.route)

        if cached is not None and len(cached) > 0:
            print()
            print(f"Route chargers cached: {len(cached)}")
            return cached

        if cached is not None and len(cached) == 0:
            print()
            print("Cached charger list was empty.")
            print("Ignoring empty cache and searching again.")

        search_points = CorridorService.sample_route(
            trip.route.geometry
        )

        print()
        print(f"Route search points: {len(search_points)}")

        chargers = await CorridorService.search_points(
            search_points
        )

        print()
        print(f"OpenChargeMap returned {len(chargers)} chargers")

        chargers = CorridorService.filter_chargers(
            chargers,
            trip
        )

        CorridorCache.set(
            trip.route,
            chargers
        )

        print()
        print(f"Route chargers after filtering: {len(chargers)}")

        return chargers

    @staticmethod
    async def find_chargers_in_window(route, window, trip):
        search_points = SearchWindowService.search_points(
            route,
            window
        )

        coordinates = [
            point["coordinate"]
            for point in search_points
        ]

        print()
        print(f"Window search points: {len(coordinates)}")

        chargers = await CorridorService.search_points(
            coordinates
        )

        print()
        print(f"OpenChargeMap returned {len(chargers)} chargers")

        chargers = CorridorService.filter_chargers(
            chargers,
            trip
        )

        print()
        print(f"Window chargers after filtering: {len(chargers)}")

        return chargers