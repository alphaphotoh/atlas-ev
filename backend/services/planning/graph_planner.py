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

            #
            # A trip that can now reach the
            # destination is complete.
            #
            if (
                node.trip.simulation.arrival_soc >=
                node.trip.planning.target_destination_soc
            ):

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

                    child.f_cost,

                    child.depth

                )

            )

            frontier.extend(
                children
            )

        return GraphOptimizer.best(
            completed
        )