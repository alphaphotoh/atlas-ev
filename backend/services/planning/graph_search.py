from backend.models.trip_node import TripNode
from backend.models.trip_itinerary import TripItinerary
from backend.models.trip_leg import TripLeg

from backend.services.planning.candidate_builder import (
    CandidateBuilder,
)
from backend.services.planning.corridor_service import (
    CorridorService,
)
from backend.services.planning.optimizer.departure_optimizer import (
    DepartureOptimizer,
)
from backend.services.planning.scoring_service import (
    ScoringService,
)
from backend.services.simulation.charging_time_service import (
    ChargingTimeService,
)


class GraphSearch:

    MAX_CANDIDATES = 12

    DETOUR_SPEED_KMH = 50

    @staticmethod
    async def expand(
        node: TripNode
    ):

        print()
        print("========== GRAPH SEARCH EXPAND ==========")

        print(
            f"Depth: {node.depth}"
        )

        print(
            f"Route distance: "
            f"{node.trip.route.distance_km:.1f} km"
        )

        print(
            f"Starting SOC: "
            f"{getattr(node.trip, 'starting_soc', 0):.1f}%"
        )

        print(
            f"Actual destination SOC: "
            f"{node.trip.battery_states[-1].soc:.1f}%"
        )

        print(
            f"Target destination SOC: "
            f"{node.trip.planning.target_destination_soc:.1f}%"
        )

        chargers = await CorridorService.find_chargers(

            node.trip

        )

        print()
        print(
            f"Chargers returned by corridor: "
            f"{len(chargers)}"
        )

        candidates = []

        rejected_low_arrival_soc = 0
        rejected_detour = 0
        rejected_visited = 0
        candidate_build_errors = 0

        for charger in chargers:

            try:

                candidate = CandidateBuilder.build(

                    trip=node.trip,

                    charger=charger

                )

            except Exception as error:

                candidate_build_errors += 1

                print()
                print(
                    "Candidate build error:"
                )

                print(
                    error
                )

                continue

            if (

                candidate.arrival_soc <

                node.trip.planning.minimum_charger_arrival_soc

            ):

                rejected_low_arrival_soc += 1

                continue

            detour_distance_km = (

                candidate.charger.detour_distance_km

                or 0.0

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

            candidates.append(

                candidate

            )

        print()
        print(
            f"Candidate build errors: "
            f"{candidate_build_errors}"
        )

        print(
            f"Rejected low arrival SOC: "
            f"{rejected_low_arrival_soc}"
        )

        print(
            f"Rejected detour: "
            f"{rejected_detour}"
        )

        print(
            f"Rejected visited charger: "
            f"{rejected_visited}"
        )

        print(
            f"Viable candidates before limit: "
            f"{len(candidates)}"
        )

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

        candidates = candidates[

            :GraphSearch.MAX_CANDIDATES

        ]

        print(
            f"Candidates considered: "
            f"{len(candidates)}"
        )

        children = []

        for candidate in candidates:

            departure_soc, next_trip = await DepartureOptimizer.optimize(

                trip=node.trip,

                charger=candidate.charger,

                arrival_soc=candidate.arrival_soc

            )

            if next_trip is None:

                continue

            candidate.departure_soc = departure_soc

            candidate.destination_arrival_soc = (

                next_trip.battery_states[-1].soc

            )

            energy_added, charging_time = ChargingTimeService.estimate(

                vehicle=node.trip.vehicle,

                charger=candidate.charger,

                arrival_soc=candidate.arrival_soc,

                target_soc=departure_soc

            )

            candidate.charge_added_kwh = energy_added

            candidate.charging_time_minutes = charging_time

            detour_distance_km = (

                candidate.charger.detour_distance_km

                or 0.0

            )

            detour_minutes = (

                detour_distance_km /

                GraphSearch.DETOUR_SPEED_KMH

            ) * 60

            candidate.total_trip_time_minutes = round(

                next_trip.route.duration_minutes +

                charging_time +

                detour_minutes,

                1

            )

            candidate.score = ScoringService.score(

                candidate,

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

                    results=candidates,

                    selected_result=candidate

                )

            )

            visited = set(

                node.visited_chargers

            )

            visited.add(

                GraphSearch.charger_id(

                    candidate.charger

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

                        candidate.total_trip_time_minutes

                    ),

                    h_cost=0.0

                )

            )

            print()
            print(
                "Child created:"
            )

            print(
                f"Charger: {candidate.charger.name}"
            )

            print(
                f"Arrival SOC: "
                f"{candidate.arrival_soc:.1f}%"
            )

            print(
                f"Departure SOC: "
                f"{candidate.departure_soc:.1f}%"
            )

            print(
                f"Destination SOC: "
                f"{candidate.destination_arrival_soc:.1f}%"
            )

            print(
                f"Power: "
                f"{candidate.charger.power_kw} kW"
            )

            print(
                f"Detour: "
                f"{candidate.charger.detour_distance_km:.2f} km"
            )

            print(
                f"Score: "
                f"{candidate.score}"
            )

        children.sort(

            key=lambda child: (

                -child.itinerary.last_leg.selected_result.score,

                child.g_cost

            )

        )

        print()
        print(
            f"Children created: "
            f"{len(children)}"
        )

        return children

    @staticmethod
    def charger_id(
        charger
    ):

        return (

            round(charger.latitude, 6),

            round(charger.longitude, 6)

        )

    @staticmethod
    def arrival_soc_penalty(
        candidate,
        planning
    ):

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