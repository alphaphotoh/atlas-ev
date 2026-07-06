from backend.services.planning.trip_builder import (
    TripBuilder,
)


class DepartureOptimizer:

    @staticmethod
    async def optimize(
        trip,
        charger,
        arrival_soc
    ):

        departure_soc = max(

            arrival_soc,

            trip.planning.ideal_charger_arrival_soc_min

        )

        departure_soc = min(

            departure_soc,

            trip.planning.road_trip_charge_limit

        )

        while True:

            next_trip = await TripBuilder.build(

                trip=trip,

                charger=charger,

                departure_soc=departure_soc

            )

            destination_soc = (

                next_trip.battery_states[-1].soc

            )

            if (

                destination_soc >=

                trip.planning.target_destination_soc

            ):

                return (

                    round(departure_soc, 1),

                    next_trip

                )

            departure_soc += 1.0

            if (

                departure_soc >

                trip.planning.road_trip_charge_limit

            ):

                return (

                    trip.planning.road_trip_charge_limit,

                    next_trip

                )