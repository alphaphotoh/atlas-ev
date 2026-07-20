from backend.models.trip_node import TripNode
from backend.models.trip_itinerary import TripItinerary
from backend.models.trip_planning_result import TripPlanningResult

from backend.services.planning.graph_search import GraphSearch
from backend.services.planning.planner_logger import PlannerLogger


class GraphPlanner:
    MAX_EXPANSIONS = 30
    MAX_COMPLETED = 2
    MAX_FRONTIER = 40

    DETOUR_SPEED_KMH = 50

    @staticmethod
    async def plan(trip):
        result = await GraphPlanner.plan_with_alternatives(
            trip
        )

        return result.recommended

    @staticmethod
    async def plan_with_alternatives(trip):
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

            return TripPlanningResult(
                recommended=root,
                completed=[root]
            )

        frontier = [root]
        completed = []
        expansions = 0

        while (
            frontier and
            expansions < GraphPlanner.MAX_EXPANSIONS and
            len(completed) < GraphPlanner.MAX_COMPLETED
        ):
            node = GraphPlanner.pop_best(
                frontier
            )

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
                    completed = GraphPlanner.add_completed(
                        completed=completed,
                        node=child
                    )

                    PlannerLogger.log()
                    PlannerLogger.log("✓ Completed child itinerary found")
                    PlannerLogger.log(f"Depth: {child.depth}")
                    PlannerLogger.log(
                        f"Unique completed itineraries: "
                        f"{len(completed)}"
                    )
                    PlannerLogger.log(
                        f"Itinerary cost: "
                        f"{GraphPlanner.itinerary_cost(child):.2f}"
                    )

                else:
                    frontier.append(child)

            frontier = GraphPlanner.prune_frontier(
                frontier
            )

            expansions += 1

        if completed:
            completed = GraphPlanner.sorted_completed(
                completed
            )

            best = completed[0]

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

            return TripPlanningResult(
                recommended=best,
                completed=completed
            )

        PlannerLogger.log()
        PlannerLogger.log("=" * 60)
        PlannerLogger.log("Completed itineraries: 0")

        return TripPlanningResult(
            recommended=None,
            completed=[]
        )

    @staticmethod
    def add_completed(completed, node):
        node_signature = GraphPlanner.completed_signature(
            node
        )

        for existing in completed:
            existing_signature = GraphPlanner.completed_signature(
                existing
            )

            if existing_signature == node_signature:
                return completed

        completed.append(
            node
        )

        completed = GraphPlanner.sorted_completed(
            completed
        )

        return completed[
            :GraphPlanner.MAX_COMPLETED
        ]

    @staticmethod
    def completed_signature(node):
        if node is None:
            return tuple()

        if node.itinerary is None:
            return tuple()

        signature = []

        for leg in node.itinerary.legs:
            candidate = leg.selected_result

            if candidate is None:
                continue

            charger = candidate.charger

            signature.append(
                (
                    round(
                        getattr(charger, "latitude", 0.0),
                        5
                    ),
                    round(
                        getattr(charger, "longitude", 0.0),
                        5
                    ),
                    round(
                        candidate.arrival_soc or 0.0,
                        1
                    ),
                    round(
                        candidate.departure_soc or 0.0,
                        1
                    )
                )
            )

        return tuple(signature)

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
    def sorted_completed(nodes):
        return sorted(
            nodes,
            key=lambda node: GraphPlanner.itinerary_cost(
                node
            )
        )

    @staticmethod
    def best_completed(nodes):
        sorted_nodes = GraphPlanner.sorted_completed(
            nodes
        )

        if not sorted_nodes:
            return None

        return sorted_nodes[0]

    @staticmethod
    def itinerary_cost(node):
        legs = node.itinerary.legs

        if not legs:
            return 0.0

        stops = len(legs)

        base_driving_minutes = GraphPlanner.base_driving_minutes(
            node
        )

        total_charging_minutes = GraphPlanner.total_charging_minutes(
            node
        )

        total_detour_minutes = GraphPlanner.total_detour_minutes(
            node
        )

        trip_time_cost = (
            base_driving_minutes +
            total_charging_minutes +
            total_detour_minutes
        )

        stop_penalty = stops * 90.0

        full_charge_penalty = 0.0
        high_departure_penalty = 0.0
        very_low_arrival_penalty = 0.0
        weak_score_penalty = 0.0

        for leg in legs:
            candidate = leg.selected_result

            if candidate is None:
                continue

            departure_soc = candidate.departure_soc or 0.0
            arrival_soc = candidate.arrival_soc or 0.0
            score = candidate.score or 0.0

            if departure_soc >= 99.5:
                full_charge_penalty += 50.0

            if departure_soc > 95.0:
                high_departure_penalty += (
                    departure_soc -
                    95.0
                ) * 2.0

            if arrival_soc < 8.0:
                very_low_arrival_penalty += (
                    8.0 -
                    arrival_soc
                ) * 8.0

            if score < 250.0:
                weak_score_penalty += (
                    250.0 -
                    score
                ) * 0.05

        final_soc = GraphPlanner.actual_arrival_soc(
            node
        )

        target_soc = node.trip.planning.target_destination_soc

        excess_final_soc_penalty = max(
            final_soc -
            target_soc,
            0.0
        ) * 1.0

        shortfall_penalty = 0.0

        if final_soc < target_soc:
            shortfall_penalty = (
                target_soc -
                final_soc
            ) * 1000.0

        cost = (
            trip_time_cost +
            stop_penalty +
            full_charge_penalty +
            high_departure_penalty +
            very_low_arrival_penalty +
            weak_score_penalty +
            excess_final_soc_penalty +
            shortfall_penalty
        )

        return round(
            cost,
            2
        )

    @staticmethod
    def base_driving_minutes(node):
        if not node.itinerary.legs:
            return 0.0

        first_leg = node.itinerary.legs[0]

        if first_leg.route is None:
            return 0.0

        return first_leg.route.duration_minutes or 0.0

    @staticmethod
    def total_charging_minutes(node):
        total = 0.0

        for leg in node.itinerary.legs:
            candidate = leg.selected_result

            if candidate is None:
                continue

            total += candidate.charging_time_minutes or 0.0

        return total

    @staticmethod
    def total_detour_minutes(node):
        total = 0.0

        for leg in node.itinerary.legs:
            candidate = leg.selected_result

            if candidate is None:
                continue

            charger = candidate.charger

            detour_km = (
                charger.detour_distance_km
                or 0.0
            )

            total += (
                detour_km /
                GraphPlanner.DETOUR_SPEED_KMH
            ) * 60

        return total

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
        if node is None:
            return 0.0

        if getattr(node.trip, "battery_states", None):
            return node.trip.battery_states[-1].soc

        simulation = getattr(
            node.trip,
            "simulation",
            None
        )

        if simulation is not None:
            return simulation.arrival_soc or 0.0

        return 0.0

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