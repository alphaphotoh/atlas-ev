class TripFeasibilityService:

    @staticmethod
    def can_reach(

        trip,

        departure_soc,

        remaining_distance

    ):

        energy_needed = (

            remaining_distance *

            trip.simulation.predicted_efficiency / 100

        )

        soc_used = (

            energy_needed /

            trip.vehicle.usable_battery_kwh

        ) * 100

        destination_soc = (

            departure_soc -

            soc_used

        )

        return (

            destination_soc >=

            trip.planning.target_destination_soc

        )