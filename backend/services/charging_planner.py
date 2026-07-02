from backend.models.charging_candidate import ChargingCandidate
from backend.services.corridor_service import CorridorService
from backend.services.search_window_service import SearchWindowService


class ChargingPlanner:

    SEARCH_SOC = 25

    @staticmethod
    async def plan(route, battery_states):

        search_state = None

        for state in battery_states:

            if state.soc <= ChargingPlanner.SEARCH_SOC:
                search_state = state
                break

        if search_state is None:
            return []

        print(
            f"Battery reaches {search_state.soc:.1f}% "
            f"at {search_state.distance_km:.1f} km"
        )

        window = SearchWindowService.build(
            route,
            search_state
        )

        print(
            f"Search Window: "
            f"{window.start_distance_km:.1f} km -> "
            f"{window.end_distance_km:.1f} km"
        )

        chargers = await CorridorService.find_chargers_in_window(
            route,
            window
        )

        candidates = []

        for charger in chargers:

            candidates.append(

                ChargingCandidate(

                    charger=charger,

                    arrival_soc=search_state.soc

                )

            )

        return candidates