from backend.models.journey import Journey

from backend.services.planning.trip_builder import TripBuilder
from backend.services.planning.trip_expander import TripExpander


class JourneyBuilder:
    INTERMEDIATE_WAYPOINT_TARGET_SOC = 65.0

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

        total_legs = len(waypoints)

        for index, waypoint in enumerate(waypoints):
            is_final_leg = index == total_legs - 1

            trip = await TripBuilder.build_trip(
                vehicle=vehicle,
                origin=waypoint.origin,
                destination=waypoint.destination,
                starting_soc=current_soc,
                average_speed=average_speed,
                highway_ratio=highway_ratio
            )

            if not is_final_leg:
                trip.planning.target_destination_soc = max(
                    trip.planning.target_destination_soc,
                    JourneyBuilder.INTERMEDIATE_WAYPOINT_TARGET_SOC
                )

            planning_result = await TripExpander.expand_with_result(
                trip
            )

            itinerary = TripExpander.itinerary_from_result(
                planning_result
            )

            journey.trips.append(
                trip
            )

            journey.itineraries.append(
                itinerary
            )

            journey.planning_results.append(
                planning_result
            )

            journey.total_distance_km += trip.route.distance_km
            journey.total_duration_minutes += trip.route.duration_minutes
            journey.total_driving_minutes += trip.route.duration_minutes
            journey.total_energy_kwh += trip.simulation.energy_needed_kwh
            journey.total_charging_minutes += itinerary.total_charging_minutes
            journey.total_trip_minutes += itinerary.total_trip_minutes
            journey.total_stops += itinerary.stops

            if itinerary.legs:
                current_soc = itinerary.destination_soc

            elif trip.battery_states:
                current_soc = trip.battery_states[-1].soc

            elif trip.simulation:
                current_soc = trip.simulation.arrival_soc

            else:
                current_soc = 0.0

        journey.arrival_soc = current_soc

        return journey