from dataclasses import dataclass


@dataclass(frozen=True)
class ChargeCurvePoint:
    soc: float
    power_kw: float


class ChargeCurve:
    DEFAULT_POINTS = (
        ChargeCurvePoint(0.0, 80.0),
        ChargeCurvePoint(10.0, 180.0),
        ChargeCurvePoint(70.0, 180.0),
        ChargeCurvePoint(85.0, 70.0),
        ChargeCurvePoint(100.0, 25.0),
    )

    def __init__(self, points=None):
        self.points = sorted(
            points or self.DEFAULT_POINTS,
            key=lambda point: point.soc
        )

    @classmethod
    def default_vf9(cls):
        return cls()

    def power_at_soc(self, soc):
        soc = self.clamp_soc(soc)

        if soc <= self.points[0].soc:
            return self.points[0].power_kw

        for index in range(1, len(self.points)):
            previous = self.points[index - 1]
            current = self.points[index]

            if soc <= current.soc:
                soc_span = current.soc - previous.soc

                if soc_span <= 0:
                    return current.power_kw

                fraction = (
                    soc -
                    previous.soc
                ) / soc_span

                return (
                    previous.power_kw +
                    fraction *
                    (
                        current.power_kw -
                        previous.power_kw
                    )
                )

        return self.points[-1].power_kw

    def effective_power_at_soc(
        self,
        soc,
        vehicle,
        charger
    ):
        curve_power = self.power_at_soc(
            soc
        )

        charger_power = getattr(
            charger,
            "power_kw",
            curve_power
        ) or curve_power

        vehicle_power = getattr(
            vehicle,
            "dc_max_kw",
            curve_power
        ) or curve_power

        return max(
            min(
                curve_power,
                charger_power,
                vehicle_power
            ),
            1.0
        )

    def energy_to_charge(
        self,
        vehicle,
        start_soc,
        end_soc
    ):
        start_soc = self.clamp_soc(
            start_soc
        )

        end_soc = self.clamp_soc(
            end_soc
        )

        if end_soc <= start_soc:
            return 0.0

        usable_battery_kwh = getattr(
            vehicle,
            "usable_battery_kwh",
            0.0
        )

        return usable_battery_kwh * (
            end_soc -
            start_soc
        ) / 100.0

    def time_to_charge(
        self,
        vehicle,
        charger,
        start_soc,
        end_soc,
        step_soc=0.5
    ):
        start_soc = self.clamp_soc(
            start_soc
        )

        end_soc = self.clamp_soc(
            end_soc
        )

        if end_soc <= start_soc:
            return 0.0

        total_minutes = 0.0
        soc = start_soc

        while soc < end_soc:
            next_soc = min(
                soc + step_soc,
                end_soc
            )

            energy_kwh = self.energy_to_charge(
                vehicle=vehicle,
                start_soc=soc,
                end_soc=next_soc
            )

            power_kw = self.effective_power_at_soc(
                soc=soc,
                vehicle=vehicle,
                charger=charger
            )

            total_minutes += (
                energy_kwh /
                power_kw
            ) * 60.0

            soc = next_soc

        return total_minutes

    def marginal_minutes_per_percent(
        self,
        vehicle,
        charger,
        soc
    ):
        soc = self.clamp_soc(
            soc
        )

        end_soc = min(
            soc + 1.0,
            100.0
        )

        if end_soc <= soc:
            return float("inf")

        return self.time_to_charge(
            vehicle=vehicle,
            charger=charger,
            start_soc=soc,
            end_soc=end_soc,
            step_soc=0.25
        ) / (
            end_soc -
            soc
        )

    def average_minutes_per_percent(
        self,
        vehicle,
        charger,
        start_soc,
        end_soc
    ):
        start_soc = self.clamp_soc(
            start_soc
        )

        end_soc = self.clamp_soc(
            end_soc
        )

        if end_soc <= start_soc:
            return float("inf")

        minutes = self.time_to_charge(
            vehicle=vehicle,
            charger=charger,
            start_soc=start_soc,
            end_soc=end_soc,
            step_soc=0.5
        )

        return minutes / (
            end_soc -
            start_soc
        )

    def efficient_soc_cap(
        self,
        vehicle,
        charger,
        planning,
        arrival_soc,
        limit_soc
    ):
        near_peak_start = getattr(
            planning,
            "near_peak_start_soc",
            10.0
        )

        near_peak_end = getattr(
            planning,
            "near_peak_end_soc",
            70.0
        )

        multiplier = getattr(
            planning,
            "marginal_cost_multiplier",
            2.0
        )

        non_final_cap = getattr(
            planning,
            "non_final_charge_cap_soc",
            85.0
        )

        average_near_peak = self.average_minutes_per_percent(
            vehicle=vehicle,
            charger=charger,
            start_soc=near_peak_start,
            end_soc=near_peak_end
        )

        threshold = average_near_peak * multiplier

        soc = max(
            arrival_soc,
            near_peak_end
        )

        soc = round(
            soc,
            1
        )

        while soc < limit_soc:
            marginal = self.marginal_minutes_per_percent(
                vehicle=vehicle,
                charger=charger,
                soc=soc
            )

            if marginal > threshold:
                return min(
                    max(
                        soc,
                        arrival_soc
                    ),
                    non_final_cap,
                    limit_soc
                )

            soc += 0.5

        return min(
            non_final_cap,
            limit_soc
        )

    @staticmethod
    def clamp_soc(soc):
        return max(
            0.0,
            min(
                100.0,
                float(soc or 0.0)
            )
        )