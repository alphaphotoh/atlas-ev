from backend.services.simulation.charge_curve import ChargeCurve


class ChargingTimeService:
    DEFAULT_CURVE = ChargeCurve.default_vf9()

    @staticmethod
    def estimate(
        vehicle,
        charger,
        arrival_soc,
        target_soc
    ):
        if target_soc <= arrival_soc:
            return 0.0, 0.0

        energy_kwh = ChargingTimeService.DEFAULT_CURVE.energy_to_charge(
            vehicle=vehicle,
            start_soc=arrival_soc,
            end_soc=target_soc
        )

        charging_minutes = ChargingTimeService.DEFAULT_CURVE.time_to_charge(
            vehicle=vehicle,
            charger=charger,
            start_soc=arrival_soc,
            end_soc=target_soc
        )

        return (
            round(energy_kwh, 1),
            round(charging_minutes, 1)
        )

    @staticmethod
    def power_at_soc(soc):
        return ChargingTimeService.DEFAULT_CURVE.power_at_soc(
            soc
        )

    @staticmethod
    def time_to_charge(
        vehicle,
        charger,
        start_soc,
        end_soc
    ):
        return ChargingTimeService.DEFAULT_CURVE.time_to_charge(
            vehicle=vehicle,
            charger=charger,
            start_soc=start_soc,
            end_soc=end_soc
        )

    @staticmethod
    def marginal_minutes_per_percent(
        vehicle,
        charger,
        soc
    ):
        return ChargingTimeService.DEFAULT_CURVE.marginal_minutes_per_percent(
            vehicle=vehicle,
            charger=charger,
            soc=soc
        )