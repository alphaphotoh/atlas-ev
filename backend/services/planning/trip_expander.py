from backend.models.trip_itinerary import TripItinerary

from backend.services.planning.graph_planner import GraphPlanner


class TripExpander:
    @staticmethod
    async def expand(trip):
        result = await TripExpander.expand_with_result(
            trip
        )

        return TripExpander.itinerary_from_result(
            result
        )

    @staticmethod
    async def expand_with_result(trip):
        result = await GraphPlanner.plan_with_alternatives(
            trip
        )

        return result

    @staticmethod
    def itinerary_from_result(result):
        if result is None:
            return TripItinerary()

        if result.recommended is None:
            return TripItinerary()

        return result.recommended.itinerary