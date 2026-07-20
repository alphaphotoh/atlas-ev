import asyncio
import copy

from backend.models.trip_node import TripNode
from backend.models.trip_itinerary import TripItinerary
from backend.models.trip_leg import TripLeg

from backend.services.planning.candidate_builder import CandidateBuilder
from backend.services.planning.corridor_service import CorridorService
from backend.services.planning.optimizer.departure_optimizer import DepartureOptimizer
from backend.services.planning.planner_logger import PlannerLogger
from backend.services.planning.scoring_service import ScoringService
from backend.services.simulation.charging_time_service import ChargingTimeService


class GraphSearch:
    MAX_CANDIDATES = 6
    MAX_CHILDREN = 8
    CHARGE_OPTION_TIMEOUT_SECONDS = 6.0

    @staticmethod
    def candidate_limit_for_trip(trip):
        route = getattr(trip, "route", None)
        distance_km = getattr(route, "distance_km", 0.0) or 0.0

        if distance_km >= 650:
            return 3

        return GraphSearch.MAX_CANDIDATES


    @staticmethod
    def child_limit_for_trip(trip):
        route = getattr(trip, "route", None)
        distance_km = getattr(route, "distance_km", 0.0) or 0.0

        if distance_km >= 650:
            return 3

        return GraphSearch.MAX_CHILDREN


    DETOUR_SPEED_KMH = 50

    @staticmethod
    async def expand(node: TripNode):
        PlannerLogger.log()
        PlannerLogger.log("========== GRAPH SEARCH EXPAND ==========")
        PlannerLogger.log(f"Depth: {node.depth}")
        PlannerLogger.log(f"Route distance: {node.trip.route.distance_km:.1f} km")
        PlannerLogger.log(f"Starting SOC: {getattr(node.trip, 'starting_soc', 0):.1f}%")

        actual_destination_soc = GraphSearch.trip_arrival_soc(
            node.trip
        )

        PlannerLogger.log(
            f"Actual destination SOC: "
            f"{actual_destination_soc:.1f}%"
        )

        PlannerLogger.log(
            f"Target destination SOC: "
            f"{node.trip.planning.target_destination_soc:.1f}%"
        )

        chargers = await CorridorService.find_chargers(
            node.trip
        )

        PlannerLogger.log()
        PlannerLogger.log(f"Chargers returned by corridor: {len(chargers)}")

        candidates = []

        rejected_low_arrival_soc = 0
        rejected_detour = 0
        rejected_visited = 0
        candidate_build_errors = 0

        min_arrival_soc = GraphSearch.minimum_arrival_soc(
            node.trip.planning
        )

        for charger in chargers:
            try:
                candidate = CandidateBuilder.build(
                    trip=node.trip,
                    charger=charger
                )
            except Exception as error:
                candidate_build_errors += 1
                PlannerLogger.log()
                PlannerLogger.log("Candidate build error:")
                PlannerLogger.log(error)
                continue

            if candidate.arrival_soc < min_arrival_soc:
                rejected_low_arrival_soc += 1
                continue

            detour_distance_km = (
                candidate.charger.detour_distance_km or 0.0
            )

            PlannerLogger.log(
                f"Candidate charger: {candidate.charger.name} | "
                f"arrival SOC: {candidate.arrival_soc:.1f}% | "
                f"detour: {detour_distance_km:.2f} km | "
                f"max detour: {node.trip.planning.maximum_detour_km:.2f} km"
            )

            if (
                detour_distance_km >
                node.trip.planning.maximum_detour_km
            ):
                rejected_detour += 1
                continue

            charger_id = GraphSearch.charger_id(
                candidate.charger
            )

            if charger_id in node.visited_chargers:
                rejected_visited += 1
                continue

            candidates.append(candidate)

        PlannerLogger.log()
        PlannerLogger.log(f"Candidate build errors: {candidate_build_errors}")
        PlannerLogger.log(f"Rejected low arrival SOC: {rejected_low_arrival_soc}")
        PlannerLogger.log(f"Rejected detour: {rejected_detour}")
        PlannerLogger.log(f"Rejected visited charger: {rejected_visited}")
        PlannerLogger.log(f"Viable candidates before limit: {len(candidates)}")

        route_distance_km = getattr(node.trip.route, "distance_km", 0.0) or 0.0

        if route_distance_km >= 700:
            candidates.sort(
                key=lambda candidate: (
                    abs((candidate.arrival_soc or 0.0) - 18.0),
                    candidate.charger.detour_distance_km or 0.0,
                    -(candidate.charger.power_kw or 0.0)
                )
            )
        else:
            candidates.sort(
                key=lambda candidate: (
                    GraphSearch.arrival_soc_penalty(
                        candidate,
                        node.trip.planning
                    ),
                    candidate.charger.detour_distance_km or 0.0,
                    -(candidate.charger.power_kw or 0.0)
                )
            )

        candidates = candidates[:GraphSearch.candidate_limit_for_trip(node.trip)]

        PlannerLogger.log(f"Candidates considered: {len(candidates)}")

        children = []

        for candidate in candidates:
            try:
                charge_options = await asyncio.wait_for(
                    DepartureOptimizer.optimize_options(
                        trip=node.trip,
                        charger=candidate.charger,
                        arrival_soc=candidate.arrival_soc
                    ),
                    timeout=GraphSearch.CHARGE_OPTION_TIMEOUT_SECONDS,
                )
            except Exception as error:
                PlannerLogger.log()
                PlannerLogger.log(
                    f"Charge option timeout/error for {candidate.charger.name}: {error}"
                )
                continue

            target_soc = node.trip.planning.target_destination_soc

            destination_reachable_from_charger = any(
                GraphSearch.trip_arrival_soc(next_trip) >= target_soc
                for _, next_trip in charge_options
                if next_trip is not None
            )

            PlannerLogger.log()
            PlannerLogger.log(
                f"Charge options for "
                f"{candidate.charger.name}: "
                f"{len(charge_options)}"
            )

            for departure_soc, next_trip in charge_options:
                if next_trip is None:
                    continue

                option_candidate = copy.deepcopy(candidate)

                option_candidate.departure_soc = departure_soc

                option_candidate.destination_arrival_soc = (
                    GraphSearch.trip_arrival_soc(next_trip)
                )

                option_candidate.requires_additional_stop = (
                    option_candidate.destination_arrival_soc <
                    target_soc
                )

                option_candidate.destination_reachable_from_charger = (
                    destination_reachable_from_charger
                )

                energy_added, charging_time = ChargingTimeService.estimate(
                    vehicle=node.trip.vehicle,
                    charger=option_candidate.charger,
                    arrival_soc=option_candidate.arrival_soc,
                    target_soc=departure_soc
                )

                option_candidate.charge_added_kwh = energy_added
                option_candidate.charging_time_minutes = charging_time

                detour_distance_km = (
                    option_candidate.charger.detour_distance_km or 0.0
                )

                detour_minutes = (
                    detour_distance_km /
                    GraphSearch.DETOUR_SPEED_KMH
                ) * 60

                option_candidate.total_trip_time_minutes = round(
                    next_trip.route.duration_minutes +
                    charging_time +
                    detour_minutes,
                    1
                )

                option_candidate.score = ScoringService.score(
                    option_candidate,
                    node.trip.planning
                )

                itinerary = TripItinerary()

                itinerary.legs.extend(
                    node.itinerary.legs
                )

                itinerary.add_leg(
                    TripLeg(
                        number=node.depth + 1,
                        route=node.trip.route,
                        battery_states=node.trip.battery_states,
                        results=[],
                        selected_result=option_candidate
                    )
                )

                visited = set(
                    node.visited_chargers
                )

                visited.add(
                    GraphSearch.charger_id(
                        option_candidate.charger
                    )
                )

                children.append(
                    TripNode(
                        trip=next_trip,
                        itinerary=itinerary,
                        depth=node.depth + 1,
                        parent=node,
                        visited_chargers=visited,
                        g_cost=(
                            node.g_cost +
                            option_candidate.total_trip_time_minutes
                        ),
                        h_cost=0.0
                    )
                )

                PlannerLogger.log()
                PlannerLogger.log("Child created:")
                PlannerLogger.log(f"Charger: {option_candidate.charger.name}")
                PlannerLogger.log(
                    f"Arrival SOC: "
                    f"{option_candidate.arrival_soc:.1f}%"
                )
                PlannerLogger.log(
                    f"Departure SOC: "
                    f"{option_candidate.departure_soc:.1f}%"
                )
                PlannerLogger.log(
                    f"Destination SOC: "
                    f"{option_candidate.destination_arrival_soc:.1f}%"
                )
                PlannerLogger.log(
                    f"Power: "
                    f"{option_candidate.charger.power_kw} kW"
                )
                PlannerLogger.log(
                    f"Detour: "
                    f"{option_candidate.charger.detour_distance_km:.2f} km"
                )
                PlannerLogger.log(
                    f"Charging minutes: "
                    f"{option_candidate.charging_time_minutes:.1f}"
                )
                PlannerLogger.log(f"Score: {option_candidate.score}")

        children.sort(
            key=lambda child: (
                child.itinerary.total_charging_minutes,
                child.itinerary.total_trip_minutes,
                -child.itinerary.last_leg.selected_result.score,
                child.g_cost
            )
        )

        children = children[:GraphSearch.child_limit_for_trip(node.trip)]

        PlannerLogger.log()
        PlannerLogger.log(f"Children created: {len(children)}")

        return children

    @staticmethod
    def trip_arrival_soc(trip):
        if trip is None:
            return 0.0

        if getattr(trip, "battery_states", None):
            return trip.battery_states[-1].soc

        simulation = getattr(
            trip,
            "simulation",
            None
        )

        if simulation is not None:
            return simulation.arrival_soc or 0.0

        return 0.0

    @staticmethod
    def minimum_arrival_soc(planning):
        return getattr(
            planning,
            "minimum_charger_arrival_soc",
            getattr(
                planning,
                "min_arrival_soc",
                10.0
            )
        )

    @staticmethod
    def charger_id(charger):
        return (
            round(charger.latitude, 6),
            round(charger.longitude, 6)
        )

    @staticmethod
    def arrival_soc_penalty(candidate, planning):
        arrival_soc = candidate.arrival_soc

        if (
            planning.ideal_charger_arrival_soc_min
            <= arrival_soc
            <= planning.ideal_charger_arrival_soc_max
        ):
            return 0.0

        if arrival_soc < planning.ideal_charger_arrival_soc_min:
            return (
                planning.ideal_charger_arrival_soc_min -
                arrival_soc
            )

        return (
            arrival_soc -
            planning.ideal_charger_arrival_soc_max
        )