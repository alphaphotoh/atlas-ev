import heapq

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

        frontier = []

        heapq.heappush(

            frontier,

            (

                *GraphOptimizer.priority(
                    root
                ),


                root

            )

        )

        completed = []

        while frontier:

            _, _, node = heapq.heappop(
                frontier
            )

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

            for child in children:

                heapq.heappush(

                    frontier,

                    (

                        *GraphOptimizer.priority(
                            child
                        ),

                        child

                    )

                )

        return GraphOptimizer.best(
            completed
        )