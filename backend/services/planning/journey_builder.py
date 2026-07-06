from backend.models.journey import Journey

from backend.services.planning.trip_builder import (
    TripBuilder,
)

from backend.services.planning.trip_expander import (
    TripExpander,
)


class JourneyBuilder:

    @staticmethod
    async def build(
        vehicle,
        waypoints,
        starting_soc,
        average_speed,
        highway_ratio
    ):

        journey = Journey()

        current_soc = starting_soc

        for waypoint in waypoints:

            trip = await TripBuilder.build_trip(

                vehicle=vehicle,

                origin=waypoint.origin,

                destination=waypoint.destination,

                starting_soc=current_soc,

                average_speed=average_speed,

                highway_ratio=highway_ratio

            )

            itinerary = await TripExpander.expand(

                trip

            )

            journey.trips.append(

                trip

            )

            journey.itineraries.append(

                itinerary

            )

            journey.total_distance_km += (

                trip.route.distance_km

            )

            journey.total_duration_minutes += (

                trip.route.duration_minutes

            )

            journey.total_energy_kwh += (

                trip.simulation.energy_needed_kwh

            )

            journey.total_driving_minutes += (

                itinerary.total_driving_minutes

            )

            journey.total_charging_minutes += (

                itinerary.total_charging_minutes

            )

            journey.total_detour_minutes += (

                itinerary.total_detour_minutes

            )

            journey.total_trip_minutes += (

                itinerary.total_trip_minutes

            )

            #
            # Count charging stops.
            #

            journey.total_stops += (

                itinerary.stops

            )

            #
            # Carry the SOC into the next leg.
            #

            if itinerary.legs:

                last_leg = itinerary.legs[-1]

                current_soc = (

                    last_leg.selected_result.destination_soc

                )

            else:

                current_soc = (

                    trip.simulation.arrival_soc

                )

        journey.arrival_soc = current_soc

        return journey