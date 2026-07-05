from backend.services.planning.graph_planner import GraphPlanner


class GraphExecutor:

    @staticmethod
    async def execute(
        trip
    ):

        node = await GraphPlanner.plan(
            trip
        )

        if node is None:

            return None

        node.itinerary.recalculate()

        print()

        print(
            f"Trip contains "
            f"{node.itinerary.stops} leg(s)"
        )

        return node.itinerary