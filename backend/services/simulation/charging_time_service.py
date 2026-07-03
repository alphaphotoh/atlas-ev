class ChargingTimeService:

    @staticmethod
    def estimate(
        vehicle,
        arrival_soc,
        target_soc
    ):

        if target_soc <= arrival_soc:
            return 0.0, 0.0

        energy_needed = (
            vehicle.usable_battery_kwh *
            (target_soc - arrival_soc) / 100
        )

        average_power = ChargingTimeService.average_power(
            arrival_soc,
            target_soc,
            vehicle.dc_max_kw
        )

        hours = energy_needed / average_power

        minutes = hours * 60

        return (
            round(energy_needed, 1),
            round(minutes, 1)
        )

    @staticmethod
    def average_power(
        arrival_soc,
        target_soc,
        peak_power
    ):

        average_soc = (
            arrival_soc + target_soc
        ) / 2

        if average_soc < 20:
            return peak_power

        elif average_soc < 40:
            return peak_power * 0.90

        elif average_soc < 60:
            return peak_power * 0.75

        elif average_soc < 80:
            return peak_power * 0.55

        elif average_soc < 90:
            return peak_power * 0.35

        return peak_power * 0.20