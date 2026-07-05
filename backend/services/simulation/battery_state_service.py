from backend.models.battery_state import BatteryState


class BatteryStateService:

    @staticmethod
    def first_below_soc(
        battery_states: list[BatteryState],
        target_soc: float
    ) -> BatteryState | None:

        for state in battery_states:

            if state.soc <= target_soc:

                return state

        return None