from backend.services.planning.graph_planner import GraphPlanner
from backend.models.trip_itinerary import TripItinerary


class GraphExecutor:

    @staticmethod
    async def execute(
        trip
    ):

        node = await GraphPlanner.plan(
            trip
        )

        #
        # Temporary fallback while graph search
        # is still under development.
        #
        if node is None:

            itinerary = TripItinerary()

            itinerary.recalculate()

            return itinerary

        node.itinerary.recalculate()

        print()

        print(
            f"Trip contains "
            f"{node.itinerary.stops} leg(s)"
        )

        return node.itinerary