from backend.models.trip_node import TripNode

from backend.services.planning.graph_optimizer import GraphOptimizer
from backend.services.planning.graph_search import GraphSearch


class GraphPlanner:

    MAX_DEPTH = 3

    @staticmethod
    async def plan(trip):

        root = TripNode(
            trip=trip
        )

        frontier = [root]

        completed = []

        while frontier:

            node = frontier.pop(0)

            if node.itinerary.completed:

                completed.append(
                    node
                )

                continue

            if node.depth >= GraphPlanner.MAX_DEPTH:

                continue

            children = await GraphSearch.expand(
                node
            )

            frontier.extend(
                children
            )

        return GraphOptimizer.best(
            completed
        )