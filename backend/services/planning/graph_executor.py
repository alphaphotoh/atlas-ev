from backend.services.planning.graph_planner import GraphPlanner


class GraphExecutor:

    @staticmethod
   async def execute(trip):

        best = await GraphPlanner.plan(
            trip
        )

        if best is None:

            return None

        return best.itinerary