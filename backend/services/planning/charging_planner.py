from backend.services.planning.candidate_builder import CandidateBuilder
from backend.services.planning.corridor_service import CorridorService
from backend.services.planning.result_printer import ResultPrinter
from backend.services.planning.optimizer.trip_optimizer import TripOptimizer
from backend.services.planning.scoring_service import ScoringService
from backend.services.planning.search_window_service import (
    SearchWindowService,
)
from backend.services.simulation.battery_state_service import (
    BatteryStateService,
)


class ChargingPlanner:

    @staticmethod
    async def plan(trip):

        search_state = BatteryStateService.first_below_soc(

            trip.battery_states,

            trip.planning.minimum_charger_arrival_soc

        )

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

        return await ChargingPlanner.plan_next_hop(

            trip=trip,

            search_state=search_state

        )

    @staticmethod
    async def plan_next_hop(
        trip,
        search_state,
        chargers=None
    ):

        if chargers is None:

            window = SearchWindowService.build(

                trip.route,

                search_state

            )

            chargers = await CorridorService.find_chargers_in_window(

                route=trip.route,

                window=window,

                trip=trip

            )

        candidates = ChargingPlanner.plan_from_state(

            trip=trip,

            search_state=search_state,

            chargers=chargers

        )

        ResultPrinter.print(
            candidates
        )

        return candidates

    @staticmethod
    def plan_from_state(
        trip,
        search_state,
        chargers
    ):

        candidates = []

        for charger in chargers:

            candidate = CandidateBuilder.build(

                trip=trip,

                charger=charger,

            )

            if (

                candidate.arrival_soc <

                trip.planning.minimum_charger_arrival_soc

            ):

                continue

            candidate.score = ScoringService.score(
                candidate,

                trip.planning
            )

            candidates.append(
                candidate
            )

        return TripOptimizer.optimize(

            candidates,

            limit=10

        )

    @staticmethod
    def best_result(results):

        if not results:

            return None

        return results[0]