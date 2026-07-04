class ChargingTimeService:

    #
    # Average charging power (kW) by SOC.
    # These are capped later by the charger's
    # available power.
    #
    VF9_CHARGING_CURVE = [

        (10, 100),

        (20, 180),

        (30, 180),

        (40, 165),

        (50, 145),

        (60, 120),

        (70, 95),

        (80, 70),

        (90, 45),

        (101, 25)

    ]

    @staticmethod
    def estimate(
        vehicle,
        charger,
        arrival_soc,
        target_soc
    ):

        if target_soc <= arrival_soc:

            return 0.0, 0.0

        total_energy = 0.0

        total_minutes = 0.0

        soc = arrival_soc

        while soc < target_soc:

            next_soc = min(

                soc + 1,

                target_soc

            )

            energy = (

                vehicle.usable_battery_kwh *

                (next_soc - soc) / 100

            )

            curve_power = (

                ChargingTimeService.power_at_soc(

                    soc

                )

            )

            charging_power = min(

                curve_power,

                charger.power_kw,

                vehicle.dc_max_kw

            )

            hours = (

                energy /

                charging_power

            )

            total_energy += energy

            total_minutes += hours * 60

            soc = next_soc

        return (

            round(total_energy, 1),

            round(total_minutes, 1)

        )

    @staticmethod
    def power_at_soc(soc):

        for limit, power in (

            ChargingTimeService

            .VF9_CHARGING_CURVE

        ):

            if soc < limit:

                return power

        return 25