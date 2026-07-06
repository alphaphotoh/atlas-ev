from backend.models.trip_node import TripNode
from backend.models.trip_itinerary import TripItinerary
from backend.models.trip_leg import TripLeg

from backend.services.planning.charging_planner import ChargingPlanner
from backend.services.planning.trip_builder import TripBuilder
from backend.services.planning.projection_service import ProjectionService
from backend.services.simulation.battery_state_service import (
    BatteryStateService,
)


class GraphSearch:

    #
    # Only consider chargers a little beyond the point
    # where the battery reaches the minimum arrival SOC.
    #
    SEARCH_MARGIN_KM = 30

    @staticmethod
    async def expand(
        node: TripNode
    ):

        search_state = BatteryStateService.first_below_soc(

            node.trip.battery_states,

            node.trip.planning.minimum_charger_arrival_soc

        )

        if search_state is None:

            print()
            print("No search state found.")

            return []

        #
        # Load corridor chargers once.
        #

        results = await ChargingPlanner.plan_next_hop(

            trip=node.trip,

            search_state=search_state

        )

        #
        # Filter to chargers that are realistically reachable
        # from the current node.
        #

        reachable_results = []

        max_distance = (

            search_state.distance_km +

            GraphSearch.SEARCH_MARGIN_KM

        )

        for result in results:

            projected = ProjectionService.project(

                node.trip.route,

                result.candidate.charger

            )

            if projected.route_distance_km <= max_distance:

                reachable_results.append(result)

        print()

        print(
            f"Reachable candidates: "
            f"{len(reachable_results)} / {len(results)}"
        )

        children = []

        for result in reachable_results:

            itinerary = TripItinerary()

            itinerary.legs.extend(

                node.itinerary.legs

            )

            itinerary.add_leg(

                TripLeg(

                    number=node.depth + 1,

                    route=node.trip.route,

                    battery_states=node.trip.battery_states,

                    results=reachable_results,

                    selected_result=result

                )

            )

            next_trip = await TripBuilder.build(

                trip=node.trip,

                charger=result.candidate.charger,

                departure_soc=result.candidate.departure_soc

            )

            children.append(

                TripNode(

                    trip=next_trip,

                    itinerary=itinerary,

                    depth=node.depth + 1,

                    parent=node,

                    g_cost=itinerary.total_trip_minutes,

                    h_cost=0.0

                )

            )

        print(
            f"Generated {len(children)} child node(s)."
        )

        return children