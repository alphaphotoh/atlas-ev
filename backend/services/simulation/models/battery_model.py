class BatteryModel:

    @staticmethod
    def destination_soc(
        vehicle,
        departure_soc,
        energy_used
    ):

        soc_used = (

            energy_used /

            vehicle.usable_battery_kwh

        ) * 100

        return departure_soc - soc_used