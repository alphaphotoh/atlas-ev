class TripTimeService:

    @staticmethod
    def estimate(

        driving_minutes,

        charging_minutes,

        detour_km,

        average_speed

    ):

        detour_minutes = (

            detour_km /

            average_speed

        ) * 60

        return (

            driving_minutes +

            charging_minutes +

            detour_minutes

        )