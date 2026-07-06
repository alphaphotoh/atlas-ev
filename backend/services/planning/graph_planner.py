from collections import deque

from backend.models.trip_node import TripNode

from backend.services.planning.graph_optimizer import GraphOptimizer
from backend.services.planning.graph_search import GraphSearch


class GraphPlanner:

    MAX_DEPTH = 3

    @staticmethod
    async def plan(
        trip
    ):

        root = TripNode(

            trip=trip

        )

        frontier = deque(

            [root]

        )

        completed = []

        while frontier:

            node = frontier.popleft()

            print()

            print("=" * 60)

            print(

                f"Depth: {node.depth}"

            )

            estimated_soc = (

                node.trip.simulation.arrival_soc

            )

            actual_soc = (

                node.trip.battery_states[-1].soc

            )

            print(

                f"Estimated arrival SOC: {estimated_soc:.2f}%"

            )

            print(

                f"Actual arrival SOC: {actual_soc:.2f}%"

            )

            print(

                "Target destination SOC:",

                node.trip.planning.target_destination_soc

            )

            #
            # A completed trip is determined by the
            # simulated battery state, not the estimate.
            #

            if (

                actual_soc >=

                node.trip.planning.target_destination_soc

            ):

                print(

                    "✓ Destination reachable"

                )

                completed.append(

                    node

                )

                continue

            if node.depth >= GraphPlanner.MAX_DEPTH:

                print(

                    "Reached max search depth."

                )

                continue

            children = await GraphSearch.expand(

                node

            )

            print(

                f"Generated {len(children)} child node(s)."

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

        print()

        print("=" * 60)

        print(

            f"Completed itineraries: {len(completed)}"

        )

        return GraphOptimizer.best(

            completed

        )