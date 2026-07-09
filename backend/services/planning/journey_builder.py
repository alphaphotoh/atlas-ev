from backend.models.journey import Journey

from backend.services.planning.trip_builder import TripBuilder
from backend.services.planning.trip_expander import TripExpander


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