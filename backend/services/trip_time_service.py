from backend.services.charging_curve_service import ChargingCurveService


class TripTimeService:

    HIGHWAY_SPEED_KMH = 110

    EXIT_AND_REJOIN_MINUTES = 4

    @staticmethod
    def estimate(
        charger,
        arrival_soc,
        route
    ):

        target_soc = 70

        charging_minutes = (
            ChargingCurveService.estimate_minutes(
                arrival_soc,
                target_soc
            )
        )

        driving_minutes = route.duration_minutes

        total_trip_minutes = (
            driving_minutes
            + charging_minutes
            + TripTimeService.EXIT_AND_REJOIN_MINUTES
        )

        return {
            "arrival_soc": arrival_soc,
            "target_soc": target_soc,
            "charging_minutes": charging_minutes,
            "total_trip_minutes": total_trip_minutes
        }