class TripOptimizer:

    @staticmethod
    def optimize(
        results,
        limit=10
    ):

        if not results:

            return []

        results.sort(

    key=lambda result: (

        -result.candidate.score,

        result.total_trip_time_minutes,

        result.candidate.charger.detour_distance_km,

        -result.destination_soc

        )

    )

        return results[:limit]