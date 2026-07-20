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
        graph_result = await GraphPlanner.plan_with_alternatives(
            trip
        )

        if TripExpander.result_is_usable(
            result=graph_result,
            trip=trip,
        ):
            return graph_result

        fallback_result = await VeryLongTripFallbackPlanner.plan(
            trip
        )

        if TripExpander.result_is_usable(
            result=fallback_result,
            trip=trip,
        ):
            return fallback_result

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

        possible_sources = [
            recommended,
            itinerary,
            result,
        ]

        for source in possible_sources:
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
                    return len(
                        value,
                    )

        legs = getattr(
            itinerary,
            "legs",
            None,
        )

        if isinstance(legs, list):
            count = 0

            for leg in legs:
                charger = getattr(
                    leg,
                    "charger",
                    None,
                )

                if charger is not None:
                    count += 1

            return count

        completed = getattr(
            result,
            "completed",
            None,
        )

        if isinstance(completed, list):
            return len(
                completed,
            )

        return 0

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
