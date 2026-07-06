from backend.models.trip_node import TripNode
from backend.models.trip_itinerary import TripItinerary
from backend.models.trip_leg import TripLeg

from backend.services.planning.candidate_builder import CandidateBuilder
from backend.services.planning.scoring_service import ScoringService
from backend.services.simulation.battery_state_service import (
    BatteryStateService,
)


class GraphSearch:

    @staticmethod
    async def expand(
        node: TripNode
    ):

        search_state = BatteryStateService.first_below_soc(

            node.trip.battery_states,

            node.trip.planning.minimum_charger_arrival_soc

        )

        if search_state is None:

            return []

        chargers = node.trip.corridor_chargers

        children = []

        for charger in chargers:

            candidate, next_trip = await CandidateBuilder.build(

                trip=node.trip,

                charger=charger

            )

            if (

                candidate.arrival_soc <

                node.trip.planning.minimum_charger_arrival_soc

            ):

                continue

            charger = candidate.charger

            charger_id = getattr(

                charger,

                "id",

                None

            )

            if charger_id is None:

                charger_id = (

                    round(charger.latitude, 6),

                    round(charger.longitude, 6)

                )

            if charger_id in node.visited_chargers:

                continue

            candidate.destination_arrival_soc = (

                next_trip.battery_states[-1].soc

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

                    results=[],

                    selected_result=candidate

                )

            )

            visited = set(

                node.visited_chargers

            )

            visited.add(

                charger_id

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

        children.sort(

            key=lambda child: (

                -child.itinerary.last_leg.selected_result.score,

                child.g_cost

            )

        )

        print()

        print(
            f"Children created: {len(children)}"
        )

        return children