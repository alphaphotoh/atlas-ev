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
    CHARGE_OPTION_TIMEOUT_SECONDS = 3.0
    DETOUR_SPEED_KMH = 50

    @staticmethod
    def candidate_limit_for_trip(trip):
        route = getattr(
            trip,
            "route",
            None,
        )

        distance_km = getattr(
            route,
            "distance_km",
            0.0,
        ) or 0.0

        if distance_km >= 650:
            return 3

        return GraphSearch.MAX_CANDIDATES

    @staticmethod
    def child_limit_for_trip(trip):
        route = getattr(
            trip,
            "route",
            None,
        )

        distance_km = getattr(
            route,
            "distance_km",
            0.0,
        ) or 0.0

        if distance_km >= 650:
            return 3

        return GraphSearch.MAX_CHILDREN

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
                    GraphSearch.power_quality_penalty(
                        candidate,
                        node.trip.planning,
                    ),
                    GraphSearch.network_quality_penalty(
                        candidate,
                        node.trip.planning,
                    ),
                    GraphSearch.backup_quality_penalty(
                        candidate,
                        node.trip.planning,
                    ),
                    candidate.charger.detour_distance_km or 0.0,
                    -GraphSearch.charger_power_kw(candidate)
                )
            )
        else:
            candidates.sort(
                key=lambda candidate: (
                    GraphSearch.arrival_soc_penalty(
                        candidate,
                        node.trip.planning
                    ),
                    GraphSearch.power_quality_penalty(
                        candidate,
                        node.trip.planning,
                    ),
                    GraphSearch.network_quality_penalty(
                        candidate,
                        node.trip.planning,
                    ),
                    GraphSearch.backup_quality_penalty(
                        candidate,
                        node.trip.planning,
                    ),
                    candidate.charger.detour_distance_km or 0.0,
                    -GraphSearch.charger_power_kw(candidate)
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

            tested_soc_targets = []

            for option_departure_soc, _option_trip in charge_options:
                try:
                    tested_soc_targets.append(
                        round(
                            float(option_departure_soc),
                            1,
                        )
                    )
                except Exception:
                    continue

            tested_soc_targets = sorted(
                set(
                    tested_soc_targets
                )
            )

            for departure_soc, next_trip in charge_options:
                if next_trip is None:
                    continue

                option_candidate = copy.deepcopy(candidate)

                option_candidate.departure_soc = departure_soc
                try:
                    selected_departure_soc = round(
                        float(departure_soc),
                        1,
                    )
                except Exception:
                    selected_departure_soc = 0.0

                common_targets = [
                    50.0,
                    55.0,
                    60.0,
                    65.0,
                    70.0,
                    75.0,
                    80.0,
                    85.0,
                    90.0,
                    95.0,
                    98.0,
                    100.0,
                ]

                nearest_common_target = min(
                    common_targets,
                    key=lambda value: abs(
                        value - selected_departure_soc
                    ),
                )

                is_common_target = (
                    abs(
                        nearest_common_target
                        - selected_departure_soc
                    )
                    <= 0.2
                )

                if selected_departure_soc >= 99.5:
                    soc_strategy_label = "Required full charge"
                    soc_strategy_reason = (
                        "Atlas tested feasible SOC targets and selected a near-full charge "
                        "because the route required it for reachability."
                    )
                elif selected_departure_soc >= 85.0:
                    soc_strategy_label = "Upper curve target"
                    soc_strategy_reason = (
                        "Atlas tested feasible SOC targets and selected a high target "
                        "because the downstream route needed more energy."
                    )
                elif is_common_target:
                    soc_strategy_label = "Planner target band"
                    soc_strategy_reason = (
                        "Atlas tested feasible SOC targets and selected this target band "
                        "after considering charging time, reachability, and downstream route needs."
                    )
                else:
                    soc_strategy_label = "Computed route target"
                    soc_strategy_reason = (
                        "Atlas tested feasible SOC targets and selected a route-specific "
                        "SOC target instead of a fixed band."
                    )

                option_candidate.soc_strategy = {
                    "source": "backend_optimizer",
                    "strategy": soc_strategy_label,
                    "reason": soc_strategy_reason,
                    "selected_target_soc": selected_departure_soc,
                    "candidate_targets": tested_soc_targets,
                    "soft_cap_soc": 85.0,
                    "nearest_common_target": round(
                        nearest_common_target,
                        1,
                    ),
                    "is_common_target": is_common_target,
                }

                option_candidate.soc_strategy_label = soc_strategy_label
                option_candidate.soc_strategy_reason = soc_strategy_reason


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

                power_quality_penalty_minutes = (
                    GraphSearch.power_quality_penalty(
                        option_candidate,
                        node.trip.planning,
                    )
                )

                option_candidate.power_quality_penalty_minutes = (
                    power_quality_penalty_minutes
                )

                network_quality_penalty_minutes = (
                    GraphSearch.network_quality_penalty(
                        option_candidate,
                        node.trip.planning,
                    )
                )

                option_candidate.network_quality_penalty_minutes = (
                    network_quality_penalty_minutes
                )

                backup_quality_penalty_minutes = (
                    GraphSearch.backup_quality_penalty(
                        option_candidate,
                        node.trip.planning,
                    )
                )

                option_candidate.backup_quality_penalty_minutes = (
                    backup_quality_penalty_minutes
                )

                option_candidate.total_trip_time_minutes = round(
                    next_trip.route.duration_minutes +
                    charging_time +
                    detour_minutes +
                    power_quality_penalty_minutes +
                    network_quality_penalty_minutes +
                    backup_quality_penalty_minutes,
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
    def charger_power_kw(candidate):
        charger = getattr(
            candidate,
            "charger",
            candidate,
        )

        fields = [
            "power_kw",
            "max_power_kw",
            "maximum_power_kw",
            "dc_power_kw",
            "rated_power_kw",
        ]

        for field in fields:
            value = getattr(
                charger,
                field,
                None,
            )

            if value is None:
                continue

            try:
                power = float(value)
            except Exception:
                continue

            if power > 0:
                return power

        connections = getattr(
            charger,
            "connections",
            None,
        )

        if not connections:
            connections = getattr(
                charger,
                "connection_info",
                None,
            )

        if not connections:
            return 0.0

        best_power = 0.0

        for connection in connections:
            for field in fields:
                if isinstance(connection, dict):
                    value = connection.get(field)
                else:
                    value = getattr(
                        connection,
                        field,
                        None,
                    )

                if value is None:
                    continue

                try:
                    power = float(value)
                except Exception:
                    continue

                if power > best_power:
                    best_power = power

        return best_power

    @staticmethod
    def power_quality_penalty(
        candidate,
        planning,
    ):
        def safe_float(value, default):
            try:
                return float(value)
            except Exception:
                return float(default)

        power_kw = GraphSearch.charger_power_kw(
            candidate
        )

        minimum_power_kw = safe_float(
            getattr(
                planning,
                "minimum_dc_power_kw",
                50.0,
            ),
            50.0,
        )

        preferred_power_kw = safe_float(
            getattr(
                planning,
                "preferred_dc_power_kw",
                150.0,
            ),
            150.0,
        )

        unknown_penalty = safe_float(
            getattr(
                planning,
                "unknown_power_penalty_minutes",
                20.0,
            ),
            20.0,
        )

        slow_penalty = safe_float(
            getattr(
                planning,
                "slow_charger_penalty_minutes",
                15.0,
            ),
            15.0,
        )

        if power_kw <= 0:
            return unknown_penalty

        if power_kw < minimum_power_kw:
            return slow_penalty + 30.0

        if power_kw < 100.0:
            return slow_penalty + round(
                (100.0 - power_kw) * 0.15,
                1,
            )

        if power_kw < preferred_power_kw:
            return round(
                min(
                    10.0,
                    (preferred_power_kw - power_kw) * 0.08,
                ),
                1,
            )

        return 0.0

    @staticmethod
    def network_quality_penalty(
        candidate,
        planning,
    ):
        def safe_float(value, default):
            try:
                return float(value)
            except Exception:
                return float(default)

        charger = getattr(
            candidate,
            "charger",
            candidate,
        )

        name = str(
            getattr(
                charger,
                "name",
                "",
            ) or ""
        ).strip()

        network = str(
            getattr(
                charger,
                "network",
                getattr(
                    charger,
                    "operator",
                    getattr(
                        charger,
                        "operator_name",
                        getattr(
                            charger,
                            "provider",
                            "",
                        ),
                    ),
                ),
            ) or ""
        ).strip()

        combined = f"{network} {name}".lower()

        unknown_network_penalty = safe_float(
            getattr(
                planning,
                "unknown_network_penalty_minutes",
                15.0,
            ),
            15.0,
        )

        weak_network_penalty = safe_float(
            getattr(
                planning,
                "weak_network_penalty_minutes",
                8.0,
            ),
            8.0,
        )

        low_reliability_penalty = safe_float(
            getattr(
                planning,
                "low_reliability_network_penalty_minutes",
                18.0,
            ),
            18.0,
        )

        trusted_tokens = [
            "electrify canada",
            "electrify america",
            "tesla",
            "chargepoint",
            "evgo",
            "flo",
            "shell recharge",
            "circle k",
            "pilot",
            "flying j",
            "ivy",
            "petro-canada",
            "mercedes",
            "gm energy",
        ]

        semi_trusted_tokens = [
            "xcharge",
            "blink",
            "ev connect",
            "volta",
            "evgateway",
        ]

        reliability_score = getattr(
            charger,
            "reliability_score",
            None,
        )

        if reliability_score is not None:
            try:
                reliability_score = float(reliability_score)
            except Exception:
                reliability_score = None

        if reliability_score is not None and reliability_score < 0.45:
            return low_reliability_penalty

        if any(token in combined for token in trusted_tokens):
            return 0.0

        if any(token in combined for token in semi_trusted_tokens):
            if "unknown" in combined or "(unknown operator)" in combined:
                return weak_network_penalty
            return max(
                0.0,
                weak_network_penalty - 4.0,
            )

        if (
            not network
            or "unknown" in network.lower()
            or "(unknown operator)" in combined
        ):
            return unknown_network_penalty

        return weak_network_penalty

    @staticmethod
    def backup_quality_penalty(
        candidate,
        planning,
    ):
        def safe_float(value, default):
            try:
                return float(value)
            except Exception:
                return float(default)

        charger = getattr(
            candidate,
            "charger",
            candidate,
        )

        availability = str(
            getattr(
                charger,
                "availability_status",
                getattr(
                    candidate,
                    "availability_status",
                    "",
                ),
            ) or ""
        ).lower()

        reliability_label = str(
            getattr(
                charger,
                "reliability_label",
                getattr(
                    candidate,
                    "reliability_label",
                    "",
                ),
            ) or ""
        ).lower()

        backup = getattr(
            charger,
            "backup_charger",
            getattr(
                candidate,
                "backup_charger",
                None,
            ),
        )

        backup_found = bool(backup)

        backup_count = getattr(
            charger,
            "backup_charger_count",
            getattr(
                candidate,
                "backup_charger_count",
                0,
            ),
        )

        try:
            backup_count = int(backup_count or 0)
        except Exception:
            backup_count = 0

        no_backup_penalty = safe_float(
            getattr(
                planning,
                "no_backup_penalty_minutes",
                7.0,
            ),
            7.0,
        )

        unknown_availability_penalty = safe_float(
            getattr(
                planning,
                "unknown_availability_penalty_minutes",
                3.0,
            ),
            3.0,
        )

        penalty = 0.0

        if not backup_found and backup_count <= 0:
            penalty += no_backup_penalty

        if "unknown" in availability:
            penalty += unknown_availability_penalty

        if "poor" in reliability_label or "low" in reliability_label:
            penalty += no_backup_penalty

        return round(penalty, 1)

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
