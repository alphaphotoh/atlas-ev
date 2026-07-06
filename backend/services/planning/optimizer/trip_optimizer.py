class TripOptimizer:

    @staticmethod
    def optimize(
        candidates,
        limit=10
    ):

        if not candidates:

            return []

        candidates.sort(

            key=lambda candidate: (

                -candidate.score,

                candidate.total_trip_time_minutes,

                candidate.charger.detour_distance_km,

                -candidate.destination_arrival_soc

            )

        )

        return candidates[:limit]