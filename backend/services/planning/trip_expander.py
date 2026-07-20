from backend.models.trip_itinerary import TripItinerary
from backend.services.planning.graph_planner import GraphPlanner
from backend.services.planning.very_long_trip_fallback_planner import VeryLongTripFallbackPlanner


class TripExpander:
    VERY_LONG_ROUTE_KM = 1000.0

    @staticmethod
    async def expand(trip):
        result = await TripExpander.expand_with_result(
            trip
        )

        return result.recommended

    @staticmethod
    async def expand_with_result(trip):
        route = getattr(
            trip,
            "route",
            None,
        )

        distance_km = getattr(
            route,
            "distance_km",
            0.0,
        ) or 0.0

        if distance_km >= TripExpander.VERY_LONG_ROUTE_KM:
            fallback_result = await VeryLongTripFallbackPlanner.plan(
                trip
            )

            if (
                fallback_result is not None
                and fallback_result.recommended is not None
            ):
                return fallback_result

        result = await GraphPlanner.plan_with_alternatives(
            trip
        )

        if result is not None and result.recommended is not None:
            return result

        fallback_result = await VeryLongTripFallbackPlanner.plan(
            trip
        )

        if (
            fallback_result is not None
            and fallback_result.recommended is not None
        ):
            return fallback_result

        return result

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

