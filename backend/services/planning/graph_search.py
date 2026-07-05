from backend.models.trip_node import TripNode
from backend.models.trip_itinerary import TripItinerary
from backend.models.trip_leg import TripLeg

from backend.services.planning.charging_planner import ChargingPlanner
from backend.services.planning.trip_builder import TripBuilder


class GraphSearch:

    @staticmethod
    async def expand(
        node: TripNode
    ):

        results = await ChargingPlanner.plan(
            node.trip
        )

        children = []

        for result in results:

            itinerary = TripItinerary()

            itinerary.legs.extend(
                node.itinerary.legs
            )

            itinerary.add_leg(

                TripLeg(

                    number=node.depth + 1,

                    route=node.trip.route,

                    battery_states=node.trip.battery_states,

                    results=results,

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

                    depth=node.depth + 1

                )

            )

        return children