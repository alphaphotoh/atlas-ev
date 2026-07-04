from backend.services.planning.candidate_builder import CandidateBuilder
from backend.services.planning.corridor_service import CorridorService
from backend.services.planning.result_printer import ResultPrinter
from backend.services.planning.optimizer.trip_optimizer import TripOptimizer
from backend.services.planning.trip_simulator import TripSimulator
from backend.services.planning.scoring_service import ScoringService


class ChargingPlanner:

    @staticmethod
    async def plan(trip):

        minimum_soc = (
            trip.planning.minimum_charger_arrival_soc
        )

        search_state = None

        for state in trip.battery_states:

            if state.soc <= minimum_soc:

                search_state = state
                break

        if search_state is None:

            print()
            print(
                "Trip can be completed without charging."
            )

            return []

        print()

        print(
            f"Battery reaches "
            f"{search_state.soc:.1f}% "
            f"at "
            f"{search_state.distance_km:.1f} km"
        )

        chargers = await CorridorService.find_chargers(

            trip

        )

        best_results = ChargingPlanner.build_results(

            trip,

            chargers,

            search_state

        )

        ResultPrinter.print(

            best_results

        )

        return best_results

    @staticmethod
    def build_results(
        trip,
        chargers,
        search_state
    ):

        trip.results = []

        for charger in chargers:

            candidate = CandidateBuilder.build(

                trip,

                charger,

                search_state

            )

            #
            # Reject chargers that cannot be reached
            # while maintaining the minimum arrival SOC.
            #
            if (
                candidate.arrival_soc <
                trip.planning.minimum_charger_arrival_soc
            ):
                continue

            result = TripSimulator.simulate(

                trip,

                candidate

            )

            #
            # Reject trips that arrive at the destination
            # below the minimum reserve.
            #
            if (
                result.destination_soc <
                trip.planning.target_destination_soc
            ):
                continue

            result.candidate.destination_arrival_soc = (
                result.destination_soc
            )

            result.candidate.score = (

                ScoringService.score(

                    result.candidate

                )

            )

            trip.results.append(

                result

            )

        trip.results.sort(

            key=lambda result: (

                -result.candidate.score,

                result.total_trip_time_minutes

            )

        )

        return TripOptimizer.optimize(

            trip.results,

            limit=10

        )

    @staticmethod
    def best_result(results):

        if not results:

            return None

        return results[0]