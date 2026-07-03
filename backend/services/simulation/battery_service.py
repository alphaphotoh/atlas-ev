class BatteryService:

    @staticmethod
    def estimate_arrival_soc(

        starting_soc: float,

        usable_battery: float,

        energy_used: float

    ):

        battery_remaining = (

            usable_battery *

            (starting_soc / 100)

        ) - energy_used

        return max(
            0,
            battery_remaining /
            usable_battery *
            100
        )