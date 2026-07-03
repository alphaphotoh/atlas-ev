from backend.services.planning.trip_simulator import TripSimulator


class CandidateEvaluator:

    @staticmethod
    def evaluate(

        trip,

        candidates

    ):

        results = []

        for candidate in candidates:

            result = TripSimulator.simulate(

                trip,

                candidate

            )

            results.append(result)

        results.sort(

            key=lambda result:
            result.total_trip_time_minutes

        )

        return results