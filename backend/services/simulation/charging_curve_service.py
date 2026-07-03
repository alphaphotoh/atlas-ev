class ChargingCurveService:

    @staticmethod
    def estimate_minutes(
        start_soc: float,
        target_soc: float
    ):

        if target_soc <= start_soc:
            return 0

        soc_added = target_soc - start_soc

        average_kw = 140

        battery_kwh = 123

        energy = battery_kwh * soc_added / 100

        hours = energy / average_kw

        return hours * 60