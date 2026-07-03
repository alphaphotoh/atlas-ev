class DepartureOptimizer:

    STEP_SOC = 1.0

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

        target_soc = arrival_soc

        while (
            target_soc <=
            trip.planning.road_trip_charge_limit
        ):

            energy_needed = (
                remaining_distance *
                trip.simulation.predicted_efficiency
                / 100
            )

            soc_used = (
                energy_needed /
                trip.vehicle.usable_battery_kwh
            ) * 100

            destination_soc = (
                target_soc -
                soc_used
            )

            if (
                destination_soc >=
                trip.planning.target_destination_soc
            ):

                return round(
                    target_soc,
                    1
                )

            target_soc += (
                DepartureOptimizer.STEP_SOC
            )

        return (
            trip.planning.road_trip_charge_limit
        )