from backend.services.planning.candidate_builder import CandidateBuilder
from backend.services.planning.corridor_service import CorridorService
from backend.services.planning.result_printer import ResultPrinter
from backend.services.planning.search_window_service import SearchWindowService
from backend.services.planning.optimizer.trip_optimizer import TripOptimizer
from backend.services.planning.trip_simulator import TripSimulator


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

        window = SearchWindowService.build(

            trip.route,

            search_state

        )

        print(

            f"Search Window: "

            f"{window['start_distance']:.1f} km"

            f" -> "

            f"{window['end_distance']:.1f} km"

        )

        chargers = await CorridorService.find_chargers_in_window(

            trip.route,

            window

        )

        candidates = []

        for charger in chargers:

            candidate = CandidateBuilder.build(

                trip,

                charger,

                search_state

            )

            candidates.append(candidate)

        trip.results = []

        for candidate in candidates:

            trip.results.append(

                TripSimulator.simulate(
                    trip,
                    candidate
                )

            )

        trip.results.sort(

            key=lambda result:
            result.total_trip_time_minutes

        )


        best_results = TripOptimizer.optimize(

            trip.results,

            limit=10

        )

        ResultPrinter.print(

            best_results

        )

        return best_results