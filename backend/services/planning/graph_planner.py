from backend.models.trip_node import TripNode
from backend.models.trip_itinerary import TripItinerary

from backend.services.planning.graph_search import GraphSearch


class GraphPlanner:
    MAX_EXPANSIONS = 20

    @staticmethod
    async def plan(trip):
        root = TripNode(
            trip=trip,
            itinerary=TripItinerary(),
            depth=0,
            parent=None,
            visited_chargers=set(),
            g_cost=0.0,
            h_cost=0.0
        )

        frontier = [root]
        completed = []
        expansions = 0

        while frontier and expansions < GraphPlanner.MAX_EXPANSIONS:
            node = GraphPlanner.pop_best(frontier)

            GraphPlanner.print_node_status(
                node=node,
                trip=trip
            )

            if GraphPlanner.is_complete(
                node=node,
                trip=trip
            ):
                print("✓ Destination reachable")
                completed.append(node)

                print()
                print("=" * 60)
                print(f"Completed itineraries: {len(completed)}")

                return GraphPlanner.best_completed(
                    completed
                )

            children = await GraphSearch.expand(
                node
            )

            print(
                f"Generated {len(children)} child node(s)."
            )

            completed_children = [
                child
                for child in children
                if GraphPlanner.is_complete(
                    node=child,
                    trip=trip
                )
            ]

            if completed_children:
                completed.extend(
                    completed_children
                )

                best = GraphPlanner.best_completed(
                    completed
                )

                print()
                print("✓ Completed child itinerary found")
                print(
                    f"Returning completed itinerary at depth {best.depth}"
                )

                print()
                print("=" * 60)
                print(f"Completed itineraries: {len(completed)}")

                return best

            frontier.extend(
                children
            )

            expansions += 1

        if completed:
            print()
            print("=" * 60)
            print(f"Completed itineraries: {len(completed)}")

            return GraphPlanner.best_completed(
                completed
            )

        print()
        print("=" * 60)
        print("Completed itineraries: 0")

        return None

    @staticmethod
    def pop_best(frontier):
        frontier.sort(
            key=lambda node: (
                node.g_cost,
                node.itinerary.total_trip_minutes,
                node.itinerary.total_charging_minutes,
                node.depth
            )
        )

        return frontier.pop(0)

    @staticmethod
    def best_completed(nodes):
        nodes.sort(
            key=lambda node: (
                node.itinerary.total_trip_minutes,
                node.itinerary.total_charging_minutes,
                node.g_cost,
                node.depth
            )
        )

        return nodes[0]

    @staticmethod
    def is_complete(node, trip):
        if not node.trip.battery_states:
            return False

        actual_soc = node.trip.battery_states[-1].soc

        return (
            actual_soc >=
            trip.planning.target_destination_soc
        )

    @staticmethod
    def print_node_status(node, trip):
        actual_soc = 0.0

        if node.trip.battery_states:
            actual_soc = node.trip.battery_states[-1].soc

        estimated_soc = 0.0

        if node.trip.simulation:
            estimated_soc = node.trip.simulation.arrival_soc

        print()
        print("=" * 60)
        print(f"Depth: {node.depth}")
        print(f"Estimated arrival SOC: {estimated_soc:.2f}%")
        print(f"Actual arrival SOC: {actual_soc:.2f}%")
        print(
            f"Target destination SOC: "
            f"{trip.planning.target_destination_soc}"
        )