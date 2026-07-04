from backend.models.battery_state import BatteryState


class BatterySimulator:

    @staticmethod
    def simulate(
        route,
        starting_soc,
        usable_battery_kwh,
        efficiency
    ):

        print()
        print("========== BATTERY SIMULATION ==========")
        print(f"Starting SOC: {starting_soc}%")
        print(f"Usable Battery: {usable_battery_kwh} kWh")
        print(f"Efficiency: {efficiency} kWh/100km")

        if route.segments:

            first = route.segments[0]

            print(f"First Segment Length: {first.length_km:.3f} km")
            print(f"First Segment Duration: {first.duration_minutes:.3f} min")

        states = []

        remaining_energy = (
            usable_battery_kwh *
            starting_soc / 100
        )

        energy_per_km = (
            efficiency / 100
        )

        elapsed_minutes = 0

        for segment in route.segments:

            energy = (
                segment.length_km *
                energy_per_km
            )

            if segment.index < 5:

                print()

                print(f"Segment {segment.index}")

                print(f"Length: {segment.length_km:.3f} km")

                print(f"Energy Used: {energy:.3f} kWh")

                print(
                    f"Remaining Before: "
                    f"{remaining_energy:.3f} kWh"
                )

            remaining_energy -= energy

            remaining_energy = max(
                remaining_energy,
                0
            )

            if segment.index < 5:

                print(
                    f"Remaining After: "
                    f"{remaining_energy:.3f} kWh"
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

                print(f"SOC: {soc:.2f}%")

            states.append(

                BatteryState(

                    segment_index=segment.index,

                    distance_km=segment.cumulative_distance_km,

                    soc=soc,

                    energy_used_kwh=energy,

                    remaining_energy_kwh=remaining_energy,

                    efficiency_kwh_per_100km=efficiency,

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