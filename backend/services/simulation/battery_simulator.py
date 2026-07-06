from backend.models.battery_state import BatteryState


class BatterySimulator:

    @staticmethod
    def simulate(
        route,
        starting_soc,
        usable_battery_kwh,
        efficiency,
        efficiency_profile=None
    ):

        print()
        print("========== BATTERY SIMULATION ==========")
        print(f"Starting SOC: {starting_soc}%")
        print(f"Usable Battery: {usable_battery_kwh} kWh")

        states = []

        remaining_energy = (
            usable_battery_kwh *
            starting_soc / 100
        )

        elapsed_minutes = 0

        for segment in route.segments:

            segment_efficiency = efficiency

            if efficiency_profile:

                closest = min(

                    efficiency_profile,

                    key=lambda sample: abs(

                        sample.distance_km -

                        segment.cumulative_distance_km

                    )

                )

                segment_efficiency = (

                    closest.efficiency

                )

            energy_per_km = (

                segment_efficiency / 100

            )

            energy = (

                segment.length_km *

                energy_per_km

            )

            remaining_energy -= energy

            remaining_energy = max(

                remaining_energy,

                0

            )

            elapsed_minutes += (

                segment.duration_minutes

            )

            soc = (

                remaining_energy /

                usable_battery_kwh

            ) * 100

            speed = 0

            if segment.duration_minutes > 0:

                speed = (

                    segment.length_km /

                    segment.duration_minutes

                ) * 60

            if segment.index < 5:

                print()

                print(
                    f"Segment {segment.index}"
                )

                print(
                    f"Distance: "
                    f"{segment.cumulative_distance_km:.1f} km"
                )

                print(
                    f"Efficiency: "
                    f"{segment_efficiency:.2f} "
                    f"kWh/100km"
                )

                print(
                    f"Length: "
                    f"{segment.length_km:.3f} km"
                )

                print(
                    f"Energy Used: "
                    f"{energy:.3f} kWh"
                )

                print(
                    f"Remaining Before: "
                    f"{remaining_energy + energy:.3f} kWh"
                )

                print(
                    f"Remaining After: "
                    f"{remaining_energy:.3f} kWh"
                )

                print(
                    f"SOC: "
                    f"{soc:.2f}%"
                )

            states.append(

                BatteryState(

                    segment_index=segment.index,

                    distance_km=segment.cumulative_distance_km,

                    soc=soc,

                    energy_used_kwh=energy,

                    remaining_energy_kwh=remaining_energy,

                    efficiency_kwh_per_100km=segment_efficiency,

                    speed_kmh=speed,

                    elapsed_time_minutes=elapsed_minutes

                )

            )

        print()

        print(
            f"Final Remaining Energy: "
            f"{remaining_energy:.2f} kWh"
        )

        print(
            f"Final SOC: "
            f"{states[-1].soc:.2f}%"
        )

        return states