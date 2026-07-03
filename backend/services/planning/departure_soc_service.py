class DepartureSOCService:

    @staticmethod
    def calculate(

        vehicle,

        remaining_distance_km,

        efficiency,

        planning

    ):

        energy_needed = (

            remaining_distance_km *

            efficiency / 100

        )

        soc_required = (

            energy_needed /

            vehicle.usable_battery_kwh

        ) * 100

        departure_soc = (

            soc_required +

            planning.safety_buffer_soc

        )

        departure_soc = max(

            departure_soc,

            planning.preferred_arrival_soc

        )

        departure_soc = min(

            departure_soc,

            planning.maximum_departure_soc

        )

        return round(
            departure_soc,
            1
        )