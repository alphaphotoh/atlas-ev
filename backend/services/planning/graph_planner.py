from collections import deque

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

        frontier = deque(
            [root]
        )

        completed = []

        while frontier:

            node = frontier.popleft()

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

            if not children:

                continue

            children.sort(

                key=lambda child: (

                    child.itinerary.total_trip_minutes,

                    child.depth

                )

            )

            frontier.extend(
                children
            )

        return GraphOptimizer.best(
            completed
        )