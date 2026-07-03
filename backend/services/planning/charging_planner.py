from backend.services.planning.candidate_builder import CandidateBuilder
from backend.services.planning.candidate_selector import CandidateSelector
from backend.services.planning.candidate_sorter import CandidateSorter
from backend.services.planning.corridor_service import CorridorService
from backend.services.planning.scoring_service import ScoringService
from backend.services.planning.search_window_service import SearchWindowService


class ChargingPlanner:

    SEARCH_SOC = 25

    @staticmethod
    async def plan(trip):

        search_state = None

        for state in trip.battery_states:

            if state.soc <= ChargingPlanner.SEARCH_SOC:

                search_state = state

                break

        if search_state is None:
            return []

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

            candidate.score = ScoringService.score(
                candidate
            )

            candidates.append(candidate)

        CandidateSorter.sort(candidates)

        best = CandidateSelector.best(
            candidates,
            limit=10
        )

        print()
        print("========== BEST CANDIDATES ==========")

        for candidate in best:

            print()

            print(candidate.charger.name)

            print(
                f"Score: {candidate.score:.1f}"
            )

            print(
                f"Arrival SOC: "
                f"{candidate.arrival_soc:.1f}%"
            )

            print(
                f"Departure SOC: "
                f"{candidate.departure_soc:.1f}%"
            )

            print(
                f"Energy Added: "
                f"{candidate.charge_added_kwh:.1f} kWh"
            )

            print(
                f"Charging Time: "
                f"{candidate.charging_time_minutes:.1f} min"
            )

            print(
                f"Detour: "
                f"{candidate.charger.detour_km:.2f} km"
            )

        return best