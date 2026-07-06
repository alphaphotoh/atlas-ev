from backend.models.trip_node import TripNode

from backend.services.planning.graph_search import GraphSearch
from backend.services.planning.graph_optimizer import (
    GraphOptimizer,
)

class GraphPlanner:

    MAX_DEPTH = 10

    @staticmethod
    async def plan(
        trip
    ):

        root = TripNode(
            trip=trip
        )

        frontier = [root]

        completed = []

        while frontier:

            node = GraphOptimizer.best(
                frontier
            )

            frontier.remove(
                node
            )

            actual_soc = (
                node.trip.battery_states[-1].soc
            )

            print()
            print("=" * 60)
            print(f"Depth: {node.depth}")
            print(
                f"Estimated arrival SOC: "
                f"{node.itinerary.destination_soc:.2f}%"
            )
            print(
                f"Actual arrival SOC: "
                f"{actual_soc:.2f}%"
            )
            print(
                f"Target destination SOC: "
                f"{node.trip.planning.target_destination_soc}"
            )

            if (
                actual_soc >=
                node.trip.planning.target_destination_soc
            ):

                print("✓ Destination reachable")

                completed.append(
                    node
                )

                continue

            if (
                node.depth >=
                GraphPlanner.MAX_DEPTH
            ):

                continue

            children = await GraphSearch.expand(
                node
            )

            print(
                f"Generated {len(children)} child node(s)."
            )

            frontier.extend(
                children
            )

        print()
        print("=" * 60)
        print(
            f"Completed itineraries: "
            f"{len(completed)}"
        )

        return GraphOptimizer.best(
            completed
        )