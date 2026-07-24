import copy

from backend.models.trip_itinerary import TripItinerary
from backend.services.planning.graph_planner import GraphPlanner
from backend.services.planning.very_long_trip_fallback_planner import (
    VeryLongTripFallbackPlanner,
)


class TripExpander:
    MIN_DIRECT_ARRIVAL_SOC = 25.0

    @staticmethod
    async def expand(trip):
        result = await TripExpander.expand_with_result(
            trip
        )

        return result.recommended

    @staticmethod
    async def expand_with_result(trip):
        graph_trip = copy.deepcopy(
            trip
        )

        fallback_trip = copy.deepcopy(
            trip
        )

        graph_result = await GraphPlanner.plan_with_alternatives(
            graph_trip
        )

        needs_charging = TripExpander.trip_needs_charging(
            trip
        )

        if not needs_charging and TripExpander.result_is_usable(
            result=graph_result,
            trip=trip,
        ):
            return graph_result

        fallback_result = await VeryLongTripFallbackPlanner.plan(
            fallback_trip
        )

        graph_usable = TripExpander.result_is_usable(
            result=graph_result,
            trip=trip,
        )

        fallback_usable = TripExpander.result_is_usable(
            result=fallback_result,
            trip=trip,
        )

        if graph_usable and fallback_usable:
            return TripExpander.better_result(
                graph_result,
                fallback_result,
                trip,
            )

        if fallback_usable:
            return fallback_result

        if graph_usable:
            return graph_result

        if (
            fallback_result is not None
            and fallback_result.recommended is not None
        ):
            return fallback_result

        return graph_result

    @staticmethod
    def result_is_usable(
        result,
        trip,
    ):
        if result is None:
            return False

        recommended = getattr(
            result,
            "recommended",
            None,
        )

        if recommended is None:
            return False

        if not TripExpander.trip_needs_charging(
            trip
        ):
            return True

        return TripExpander.charging_stop_count(
            result
        ) > 0

    @staticmethod
    def trip_needs_charging(trip):
        direct_arrival_soc = TripExpander.direct_arrival_soc(
            trip
        )

        target_soc = TripExpander.target_destination_soc(
            trip
        )

        return direct_arrival_soc < target_soc

    @staticmethod
    def direct_arrival_soc(trip):
        distance_km = VeryLongTripFallbackPlanner.route_distance_km(
            trip
        )

        efficiency = VeryLongTripFallbackPlanner.efficiency(
            trip
        )

        usable_battery = VeryLongTripFallbackPlanner.usable_battery_kwh(
            trip
        )

        starting_soc = TripExpander.starting_soc(
            trip
        )

        if usable_battery <= 0:
            return 0.0

        energy_needed_kwh = (
            distance_km
            * efficiency
            / 100.0
        )

        soc_needed = (
            energy_needed_kwh
            / usable_battery
            * 100.0
        )

        return round(
            max(
                0.0,
                starting_soc - soc_needed,
            ),
            1,
        )

    @staticmethod
    def starting_soc(trip):
        for source in [
            trip,
            getattr(trip, "simulation", None),
            getattr(trip, "battery", None),
        ]:
            if source is None:
                continue

            for name in [
                "starting_soc",
                "starting_soc_percent",
                "initial_soc",
                "current_soc",
                "soc",
            ]:
                value = getattr(
                    source,
                    name,
                    None,
                )

                if value is None:
                    continue

                try:
                    return float(value)
                except Exception:
                    continue

        return 100.0

    @staticmethod
    def target_destination_soc(trip):
        try:
            return float(
                VeryLongTripFallbackPlanner.target_destination_soc(
                    trip
                )
            )
        except Exception:
            return TripExpander.MIN_DIRECT_ARRIVAL_SOC

    @staticmethod
    def charging_stop_count(result):
        recommended = getattr(
            result,
            "recommended",
            None,
        )

        if recommended is None:
            return 0

        itinerary = getattr(
            recommended,
            "itinerary",
            None,
        )

        for source in [
            recommended,
            itinerary,
            result,
        ]:
            if source is None:
                continue

            for attribute_name in [
                "charging_stops",
                "stops",
                "completed",
            ]:
                value = getattr(
                    source,
                    attribute_name,
                    None,
                )

                if isinstance(value, list):
                    return len(value)

        legs = getattr(
            itinerary,
            "legs",
            None,
        )

        if isinstance(legs, list):
            return sum(
                1
                for leg in legs
                if getattr(leg, "charger", None) is not None
            )

        completed = getattr(
            result,
            "completed",
            None,
        )

        if isinstance(completed, list):
            return len(completed)

        return 0

    @staticmethod
    def better_result(
        first_result,
        second_result,
        trip,
    ):
        first_minutes = TripExpander.result_total_minutes(
            first_result,
            trip,
        )

        second_minutes = TripExpander.result_total_minutes(
            second_result,
            trip,
        )

        if second_minutes < first_minutes:
            return second_result

        return first_result
    @staticmethod
    def result_total_minutes(
        result,
        trip,
    ):
        itinerary = TripExpander.itinerary_from_result(
            result
        )

        route = getattr(
            trip,
            "route",
            None,
        )

        driving_minutes = getattr(
            route,
            "duration_minutes",
            0.0,
        ) or 0.0

        charging_minutes = 0.0
        detour_minutes = 0.0

        for leg in getattr(
            itinerary,
            "legs",
            [],
        ):
            candidate = getattr(
                leg,
                "selected_result",
                None,
            )

            if candidate is None:
                continue

            charging_minutes += float(
                getattr(
                    candidate,
                    "charging_time_minutes",
                    0.0,
                ) or 0.0
            )

            charger = getattr(
                candidate,
                "charger",
                None,
            )

            detour_km = getattr(
                charger,
                "detour_distance_km",
                0.0,
            ) or 0.0

            # Same rough detour conversion currently used in TripService:
            # 14.07 km -> about 16.9 min.
            detour_minutes += float(detour_km) * 1.2

        return (
            float(driving_minutes)
            + charging_minutes
            + detour_minutes
        )

    @staticmethod
    def itinerary_from_result(result):
        if result is None:
            return TripItinerary()

        recommended = getattr(
            result,
            "recommended",
            None,
        )

        if recommended is None:
            return TripItinerary()

        itinerary = getattr(
            recommended,
            "itinerary",
            None,
        )

        if itinerary is None:
            return TripItinerary()

        return itinerary

    @staticmethod
    def completed_from_result(result):
        if result is None:
            return []

        completed = getattr(
            result,
            "completed",
            None,
        )

        return completed or []
