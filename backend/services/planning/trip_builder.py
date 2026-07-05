from backend.models.trip_plan import TripPlan

from backend.services.adapters.routing_service import RoutingService
from backend.services.simulation.battery_simulator import BatterySimulator


class TripBuilder:

    @staticmethod
    async def build(
        trip,
        charger,
        departure_soc
    ):

        route = await TripBuilder.build_route(

            trip,

            charger

        )

        next_trip = TripPlan(

            vehicle=trip.vehicle,

            route=route

        )

        next_trip.planning = trip.planning

        next_trip.simulation = trip.simulation

        next_trip.corridor_chargers = (
            trip.corridor_chargers
        )

        next_trip.battery_states = (

            BatterySimulator.simulate(

                route=route,

                starting_soc=departure_soc,

                usable_battery_kwh=trip.vehicle.usable_battery_kwh,

                efficiency=trip.simulation.predicted_efficiency

            )

        )

        next_trip.remaining_distance_km = (
            route.distance_km
        )

        next_trip.starting_soc = (
            departure_soc
        )

        return next_trip

    @staticmethod
    async def build_route(
        trip,
        charger
    ):

        destination = trip.route.geometry[-1]

        return await RoutingService.get_route(

            [
                charger.longitude,
                charger.latitude
            ],

            destination

        )