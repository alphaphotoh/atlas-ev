from backend.models.battery_state import BatteryState


class BatterySimulator:

    @staticmethod
    def simulate(
        route,
        starting_soc,
        usable_battery_kwh,
        efficiency
    ):

        states = []

        remaining_energy = (
            usable_battery_kwh *
            starting_soc / 100
        )

        energy_per_km = efficiency / 100

        for segment in route.segments:

            energy = segment.length_km * energy_per_km

            remaining_energy -= energy

            remaining_energy = max(
                remaining_energy,
                0
            )

            soc = (
                remaining_energy /
                usable_battery_kwh
            ) * 100

            states.append(

                BatteryState(

                    segment_index=segment.index,

                    distance_km=segment.cumulative_distance_km,

                    soc=soc,

                    energy_used_kwh=energy

                )

            )

        return states