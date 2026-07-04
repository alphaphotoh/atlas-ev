class DepartureOptimizer:

    @staticmethod
    def optimize(
        trip,
        charger,
        arrival_soc
    ):

        remaining_distance = (

            trip.route.distance_km -

            charger.route_distance_km

        )

        energy_needed = (

            remaining_distance *

            trip.simulation.predicted_efficiency /

            100

        )

        soc_needed = (

            energy_needed /

            trip.vehicle.usable_battery_kwh

        ) * 100

        departure_soc = (

            soc_needed +

            trip.planning.target_destination_soc

        )

        departure_soc = max(

            departure_soc,

            arrival_soc

        )

        departure_soc = min(

            departure_soc,

            trip.planning.road_trip_charge_limit

        )

        return round(

            departure_soc,

            1

        )