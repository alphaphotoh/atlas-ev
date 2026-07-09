from backend.models.trip_node import TripNode
from backend.models.trip_itinerary import TripItinerary

from backend.services.planning.graph_search import GraphSearch
from backend.services.planning.planner_logger import PlannerLogger


class GraphPlanner:
    MAX_EXPANSIONS = 5
    MAX_COMPLETED = 8
    MAX_FRONTIER = 16

    DETOUR_SPEED_KMH = 50

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

        if GraphPlanner.is_complete(root, trip):
            GraphPlanner.print_node_status(
                node=root,
                trip=trip
            )

            PlannerLogger.log("✓ Destination reachable")
            PlannerLogger.log()
            PlannerLogger.log("=" * 60)
            PlannerLogger.log("Completed itineraries: 1")

            return root

        frontier = [root]
        completed = []
        expansions = 0

        while (
            frontier and
            expansions < GraphPlanner.MAX_EXPANSIONS and
            len(completed) < GraphPlanner.MAX_COMPLETED
        ):
            node = GraphPlanner.pop_best(frontier)

            GraphPlanner.print_node_status(
                node=node,
                trip=trip
            )

            children = await GraphSearch.expand(
                node
            )

            PlannerLogger.log(
                f"Generated {len(children)} child node(s)."
            )

            for child in children:
                if GraphPlanner.is_complete(
                    node=child,
                    trip=trip
                ):
                    PlannerLogger.log()
                    PlannerLogger.log("✓ Completed child itinerary found")
                    PlannerLogger.log(f"Depth: {child.depth}")
                    PlannerLogger.log(
                        f"Itinerary cost: "
                        f"{GraphPlanner.itinerary_cost(child):.2f}"
                    )

                    completed.append(child)

                else:
                    frontier.append(child)

            frontier = GraphPlanner.prune_frontier(
                frontier
            )

            expansions += 1

        if completed:
            best = GraphPlanner.best_completed(
                completed
            )

            PlannerLogger.log()
            PlannerLogger.log("✓ Best completed itinerary selected")
            PlannerLogger.log(
                f"Returning completed itinerary at depth {best.depth}"
            )
            PlannerLogger.log(
                f"Best itinerary cost: "
                f"{GraphPlanner.itinerary_cost(best):.2f}"
            )

            PlannerLogger.log()
            PlannerLogger.log("=" * 60)
            PlannerLogger.log(
                f"Completed itineraries: {len(completed)}"
            )

            return best

        PlannerLogger.log()
        PlannerLogger.log("=" * 60)
        PlannerLogger.log("Completed itineraries: 0")

        return None

    @staticmethod
    def pop_best(frontier):
        frontier.sort(
            key=lambda node: GraphPlanner.node_priority(
                node
            )
        )

        return frontier.pop(0)

    @staticmethod
    def prune_frontier(frontier):
        frontier.sort(
            key=lambda node: GraphPlanner.node_priority(
                node
            )
        )

        return frontier[
            :GraphPlanner.MAX_FRONTIER
        ]

    @staticmethod
    def node_priority(node):
        return (
            node.depth,
            GraphPlanner.itinerary_cost(node),
            node.g_cost
        )

    @staticmethod
    def best_completed(nodes):
        nodes.sort(
            key=lambda node: GraphPlanner.itinerary_cost(
                node
            )
        )

        return nodes[0]

    @staticmethod
    def itinerary_cost(node):
        legs = node.itinerary.legs

        if not legs:
            return 0.0

        stops = len(legs)

        total_trip_minutes = (
            node.itinerary.total_trip_minutes
            or node.g_cost
            or 0.0
        )

        total_charging_minutes = (
            node.itinerary.total_charging_minutes
            or 0.0
        )

        total_detour_minutes = 0.0
        full_charge_penalty = 0.0
        low_score_penalty = 0.0
        excessive_soc_added_penalty = 0.0

        for leg in legs:
            candidate = leg.selected_result

            if candidate is None:
                continue

            detour_km = (
                candidate.charger.detour_distance_km
                or 0.0
            )

            total_detour_minutes += (
                detour_km /
                GraphPlanner.DETOUR_SPEED_KMH
            ) * 60

            if candidate.departure_soc >= 99.5:
                full_charge_penalty += 150.0

            score = (
                candidate.score
                or 0.0
            )

            if score < 500.0:
                low_score_penalty += (
                    500.0 -
                    score
                ) * 0.2

            soc_added = max(
                candidate.departure_soc -
                candidate.arrival_soc,
                0.0
            )

            if soc_added > 70.0:
                excessive_soc_added_penalty += (
                    soc_added -
                    70.0
                ) * 8.0

        final_soc = GraphPlanner.actual_arrival_soc(
            node
        )

        target_soc = (
            node.trip.planning.target_destination_soc
        )

        excess_final_soc_penalty = max(
            final_soc -
            target_soc,
            0.0
        ) * 2.0

        cost = (
            total_trip_minutes +
            total_charging_minutes * 0.8 +
            total_detour_minutes * 3.0 +
            stops * 120.0 +
            full_charge_penalty +
            low_score_penalty +
            excessive_soc_added_penalty +
            excess_final_soc_penalty
        )

        return round(
            cost,
            2
        )

    @staticmethod
    def is_complete(node, trip):
        actual_soc = GraphPlanner.actual_arrival_soc(
            node
        )

        return (
            actual_soc >=
            trip.planning.target_destination_soc
        )

    @staticmethod
    def actual_arrival_soc(node):
        if not node.trip.battery_states:
            return 0.0

        return node.trip.battery_states[-1].soc

    @staticmethod
    def print_node_status(node, trip):
        actual_soc = GraphPlanner.actual_arrival_soc(
            node
        )

        estimated_soc = 0.0

        if node.trip.simulation:
            estimated_soc = node.trip.simulation.arrival_soc

        PlannerLogger.log()
        PlannerLogger.log("=" * 60)
        PlannerLogger.log(f"Depth: {node.depth}")
        PlannerLogger.log(f"Estimated arrival SOC: {estimated_soc:.2f}%")
        PlannerLogger.log(f"Actual arrival SOC: {actual_soc:.2f}%")
        PlannerLogger.log(
            f"Target destination SOC: "
            f"{trip.planning.target_destination_soc}"
        )