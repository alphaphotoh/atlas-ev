from backend.models.trip_itinerary import TripItinerary
from backend.models.trip_leg import TripLeg

from backend.services.planning.charging_planner import ChargingPlanner
from backend.services.planning.trip_builder import TripBuilder


class TripExpander:

    MAX_STOPS = 2

    @staticmethod
    async def expand(trip):

        itinerary = TripItinerary()

        await TripExpander.plan_leg(

            trip=trip,

            stop_number=1,

            itinerary=itinerary

        )

        itinerary.recalculate()

        print()

        print(
            f"Trip contains "
            f"{itinerary.stops} leg(s)"
        )

        return itinerary

    @staticmethod
    async def plan_leg(
        trip,
        stop_number,
        itinerary
    ):

        results = await ChargingPlanner.plan(
            trip
        )

        if not results:
            return

        best_result = ChargingPlanner.best_result(
            results
        )

        if best_result is None:
            return

        leg = TripLeg(

            number=stop_number,

            route=trip.route,

            battery_states=trip.battery_states,

            results=results,

            selected_result=best_result

        )

        itinerary.add_leg(
            leg
        )

        print()

        print(
            f"========== LEG {stop_number} =========="
        )

        print(
            f"Selected Charger: "
            f"{best_result.candidate.charger.name}"
        )

        print(
            f"Arrival SOC: "
            f"{best_result.candidate.arrival_soc:.1f}%"
        )

        print(
            f"Departure SOC: "
            f"{best_result.candidate.departure_soc:.1f}%"
        )

        print(
            f"Destination SOC: "
            f"{best_result.destination_soc:.1f}%"
        )

        print(
            f"Requires Another Stop: "
            f"{best_result.requires_additional_stop}"
        )

        if (
            best_result.requires_additional_stop
            and
            stop_number < TripExpander.MAX_STOPS
        ):

            await TripExpander.build_next_leg(

                trip,

                best_result,

                stop_number + 1,

                itinerary

            )

    @staticmethod
    async def build_next_leg(
        trip,
        best_result,
        stop_number,
        itinerary
    ):

        print()

        print("========== NEXT LEG ==========")

        print(
            f"Starting Leg {stop_number} with "
            f"{best_result.candidate.departure_soc:.1f}%"
        )

        next_trip = await TripBuilder.build(

            trip=trip,

            charger=best_result.candidate.charger,

            departure_soc=best_result.candidate.departure_soc

        )

        print(
            f"Second leg battery states: "
            f"{len(next_trip.battery_states)}"
        )

        await TripExpander.plan_leg(

            trip=next_trip,

            stop_number=stop_number,

            itinerary=itinerary

        )