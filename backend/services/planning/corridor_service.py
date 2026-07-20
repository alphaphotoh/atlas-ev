import asyncio
import math

from backend.services.adapters.charger_service import ChargerService
from backend.services.planning.corridor_cache import CorridorCache
from backend.services.planning.planner_logger import PlannerLogger
from backend.services.planning.search_window_service import SearchWindowService


class CorridorService:
    DEFAULT_SPACING_KM = 40
    SEARCH_RADIUS_KM = 30
    SEARCH_BATCH_SIZE = 8
    FALLBACK_MIN_POWER_KW = 50
    SEARCH_TIMEOUT_SECONDS = 5.0
    MAX_SEARCH_POINTS = 28

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
    def route_distance_km(trip):
        route = getattr(trip, "route", None)
        return getattr(route, "distance_km", 0.0) or 0.0

    @staticmethod
    def starting_soc(trip):
        value = getattr(trip, "starting_soc", 100.0)

        try:
            return float(value)
        except Exception:
            return 100.0

    @staticmethod
    def next_stop_window_km(trip):
        start_soc = CorridorService.starting_soc(trip)
        usable_soc = max(25.0, start_soc - 10.0)
        estimated_full_range_km = 425.0
        reachable_km = estimated_full_range_km * (usable_soc / 100.0)

        window_start = max(80.0, reachable_km * 0.55)
        window_end = max(window_start + 160.0, reachable_km * 1.15)

        return (
            round(window_start, 1),
            round(window_end, 1),
        )

    @staticmethod
    def search_radius_for_trip(trip):
        distance_km = CorridorService.route_distance_km(trip)

        if distance_km >= 1000:
            return 95

        if distance_km >= 650:
            return 80

        return CorridorService.SEARCH_RADIUS_KM

    @staticmethod
    def limit_search_points(points, max_points=None):
        if max_points is None:
            max_points = CorridorService.MAX_SEARCH_POINTS

        if not points:
            return []

        if len(points) <= max_points:
            return points

        selected = []

        for index in range(max_points):
            source_index = round(
                index * (len(points) - 1) / (max_points - 1)
            )
            selected.append(points[source_index])

        deduped = []

        for point in selected:
            if point not in deduped:
                deduped.append(point)

        return deduped

    @staticmethod
    def sample_route_window(coordinates, start_km, end_km, spacing_km=25):
        if not coordinates:
            return []

        points = []
        total_km = 0.0
        last_added_km = None
        previous = coordinates[0]

        for point in coordinates[1:]:
            total_km += CorridorService.distance_km(
                previous,
                point,
            )

            if start_km <= total_km <= end_km:
                if last_added_km is None or total_km - last_added_km >= spacing_km:
                    points.append(point)
                    last_added_km = total_km

            if total_km > end_km:
                break

            previous = point

        return points

    @staticmethod
    def search_points_for_trip(trip):
        route_distance = CorridorService.route_distance_km(trip)
        geometry = getattr(trip.route, "geometry", [])

        if route_distance >= 650:
            start_km, end_km = CorridorService.next_stop_window_km(trip)

            points = CorridorService.sample_route_window(
                geometry,
                start_km=start_km,
                end_km=end_km,
                spacing_km=18,
            )

            points = CorridorService.limit_search_points(
                points,
                max_points=14,
            )

            if points:
                PlannerLogger.log()
                PlannerLogger.log(
                    f"Next-stop search window: {start_km}-{end_km} km"
                )

                return points

        points = CorridorService.sample_route(
            geometry,
            spacing_km=75 if route_distance >= 1000 else CorridorService.DEFAULT_SPACING_KM,
        )

        return CorridorService.limit_search_points(
            points,
            max_points=16,
        )


    @staticmethod
    def sample_route_window(coordinates, start_km, end_km, spacing_km=25):
        if not coordinates:
            return []

        points = []
        total_km = 0.0
        last_added_km = None
        previous = coordinates[0]

        for point in coordinates[1:]:
            segment_km = CorridorService.distance_km(
                previous,
                point
            )

            total_km += segment_km

            if start_km <= total_km <= end_km:
                if last_added_km is None or total_km - last_added_km >= spacing_km:
                    points.append(point)
                    last_added_km = total_km

            if total_km > end_km:
                break

            previous = point

        return points

    @staticmethod
    def search_points_for_trip(trip):
        route_distance = CorridorService.route_distance_km(trip)
        geometry = getattr(trip.route, "geometry", [])

        if route_distance >= 700:
            start_km, end_km = CorridorService.next_stop_window_km(trip)

            points = CorridorService.sample_route_window(
                geometry,
                start_km=start_km,
                end_km=end_km,
                spacing_km=22,
            )

            points = CorridorService.limit_search_points(
                points,
                max_points=10,
            )

            if points:
                PlannerLogger.log()
                PlannerLogger.log(
                    f"Next-stop search window: {start_km}-{end_km} km"
                )

                return points

        points = CorridorService.sample_route(
            geometry,
            spacing_km=90 if route_distance >= 1000 else CorridorService.DEFAULT_SPACING_KM,
        )

        return CorridorService.limit_search_points(
            points,
            max_points=18 if route_distance >= 1000 else CorridorService.MAX_SEARCH_POINTS,
        )

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
    async def search_point(point, radius_km=None):
        if radius_km is None:
            radius_km = CorridorService.SEARCH_RADIUS_KM

        try:
            chargers = await asyncio.wait_for(
                ChargerService.search(
                    latitude=point[1],
                    longitude=point[0],
                    distance_km=radius_km,
                ),
                timeout=CorridorService.SEARCH_TIMEOUT_SECONDS,
            )

            return chargers or []

        except asyncio.TimeoutError:
            PlannerLogger.log()
            PlannerLogger.log(
                f"Charger search timed out near {point}."
            )
            return []

        except Exception as error:
            PlannerLogger.log()
            PlannerLogger.log("Charger search failed")
            PlannerLogger.log(error)
            return []


    @staticmethod
    async def search_points(points, radius_km=None):
        all_chargers = []

        if not points:
            return all_chargers

        total_batches = math.ceil(
            len(points) / CorridorService.SEARCH_BATCH_SIZE
        )

        for index in range(
            0,
            len(points),
            CorridorService.SEARCH_BATCH_SIZE,
        ):
            batch = points[
                index:index + CorridorService.SEARCH_BATCH_SIZE
            ]

            batch_number = (
                index // CorridorService.SEARCH_BATCH_SIZE
            ) + 1

            PlannerLogger.log(
                f"Searching charger batch "
                f"{batch_number} of {total_batches}"
            )

            try:
                results = await asyncio.wait_for(
                    asyncio.gather(
                        *[
                            CorridorService.search_point(
                                point,
                                radius_km=radius_km,
                            )
                            for point in batch
                        ],
                        return_exceptions=True,
                    ),
                    timeout=CorridorService.SEARCH_TIMEOUT_SECONDS + 2.0,
                )
            except asyncio.TimeoutError:
                PlannerLogger.log()
                PlannerLogger.log(
                    f"Charger batch {batch_number} timed out."
                )
                continue

            for group in results:
                if isinstance(group, Exception):
                    continue

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
        PlannerLogger.log()
        PlannerLogger.log(f"Filtering {len(chargers)} chargers")

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

        PlannerLogger.log(f"No location: {removed_no_location}")
        PlannerLogger.log(f"No power: {removed_no_power}")
        PlannerLogger.log(f"Below {minimum_power_kw} kW: {removed_low_power}")
        PlannerLogger.log(f"Unsupported connector: {removed_connector}")
        PlannerLogger.log(f"Remaining after strict filter: {len(strict)}")

        if strict:
            return list(strict.values())

        PlannerLogger.log()
        PlannerLogger.log("No chargers passed strict filter.")
        PlannerLogger.log(
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

        PlannerLogger.log(f"Fallback no location: {fallback_no_location}")
        PlannerLogger.log(f"Fallback no power: {fallback_no_power}")
        PlannerLogger.log(
            f"Fallback below "
            f"{CorridorService.FALLBACK_MIN_POWER_KW} kW: "
            f"{fallback_low_power}"
        )
        PlannerLogger.log(f"Fallback unsupported connector: {fallback_connector}")
        PlannerLogger.log(f"Remaining after fallback filter: {len(fallback)}")

        return list(fallback.values())

    @staticmethod
    async def find_chargers(trip):
        cached = CorridorCache.get(trip.route)

        if cached is not None and len(cached) > 0:
            PlannerLogger.log()
            PlannerLogger.log(f"Route chargers cached: {len(cached)}")
            return cached

        if cached is not None and len(cached) == 0:
            PlannerLogger.log()
            PlannerLogger.log("Cached charger list was empty.")
            PlannerLogger.log("Ignoring empty cache and searching again.")

        radius_km = CorridorService.search_radius_for_trip(
            trip
        )

        search_points = CorridorService.search_points_for_trip(
            trip
        )

        PlannerLogger.log()
        PlannerLogger.log(f"Route search points: {len(search_points)}")
        PlannerLogger.log(f"Route search radius km: {radius_km}")

        chargers = await CorridorService.search_points(
            search_points,
            radius_km=radius_km,
        )

        PlannerLogger.log()
        PlannerLogger.log(f"OpenChargeMap returned {len(chargers)} chargers")

        chargers = CorridorService.filter_chargers(
            chargers,
            trip
        )

        CorridorCache.set(
            trip.route,
            chargers
        )

        PlannerLogger.log()
        PlannerLogger.log(f"Route chargers after filtering: {len(chargers)}")

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

        PlannerLogger.log()
        PlannerLogger.log(f"Window search points: {len(coordinates)}")

        coordinates = CorridorService.limit_search_points(
            coordinates,
            max_points=12,
        )

        chargers = await CorridorService.search_points(
            coordinates,
            radius_km=CorridorService.search_radius_for_trip(trip),
        )

        PlannerLogger.log()
        PlannerLogger.log(f"OpenChargeMap returned {len(chargers)} chargers")

        chargers = CorridorService.filter_chargers(
            chargers,
            trip
        )

        PlannerLogger.log()
        PlannerLogger.log(f"Window chargers after filtering: {len(chargers)}")

        return chargers