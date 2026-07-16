from backend.models.battery_state import BatteryState

from backend.services.routing.route_segment_service import (
    RouteSegmentService,
)


class BatterySimulator:
    DEBUG = False
    DEBUG_SEGMENT_LIMIT = 5

    @staticmethod
    def simulate(
        route,
        starting_soc,
        usable_battery_kwh,
        efficiency,
        efficiency_profile=None,
        debug=None
    ):
        if debug is None:
            debug = BatterySimulator.DEBUG

        if debug:
            print()
            print("========== BATTERY SIMULATION ==========")
            print(f"Starting SOC: {starting_soc}%")
            print(f"Usable Battery: {usable_battery_kwh} kWh")

        states = []

        remaining_energy = (
            usable_battery_kwh *
            starting_soc /
            100
        )

        elapsed_minutes = 0.0

        segments = RouteSegmentService.segments_for_route(
            route
        )

        for segment in segments:
            segment_efficiency = efficiency

            if efficiency_profile:
                closest = min(
                    efficiency_profile,
                    key=lambda sample: abs(
                        sample.distance_km -
                        segment.cumulative_distance_km
                    )
                )

                segment_efficiency = closest.efficiency

            energy_per_km = (
                segment_efficiency /
                100
            )

            energy_used = (
                segment.length_km *
                energy_per_km
            )

            remaining_before = remaining_energy

            remaining_energy -= energy_used

            remaining_energy = max(
                remaining_energy,
                0.0
            )

            elapsed_minutes += segment.duration_minutes

            soc = (
                remaining_energy /
                usable_battery_kwh
            ) * 100

            speed_kmh = 0.0

            if segment.duration_minutes > 0:
                speed_kmh = (
                    segment.length_km /
                    segment.duration_minutes
                ) * 60

            if (
                debug and
                segment.index < BatterySimulator.DEBUG_SEGMENT_LIMIT
            ):
                print()
                print(f"Segment {segment.index}")
                print(
                    f"Distance: "
                    f"{segment.cumulative_distance_km:.1f} km"
                )
                print(
                    f"Efficiency: "
                    f"{segment_efficiency:.2f} kWh/100km"
                )
                print(
                    f"Length: "
                    f"{segment.length_km:.3f} km"
                )
                print(
                    f"Energy Used: "
                    f"{energy_used:.3f} kWh"
                )
                print(
                    f"Remaining Before: "
                    f"{remaining_before:.3f} kWh"
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
                    energy_used_kwh=energy_used,
                    remaining_energy_kwh=remaining_energy,
                    efficiency_kwh_per_100km=segment_efficiency,
                    speed_kmh=speed_kmh,
                    elapsed_time_minutes=elapsed_minutes
                )
            )

        if debug:
            print()

            if states:
                print(
                    f"Final Remaining Energy: "
                    f"{remaining_energy:.2f} kWh"
                )
                print(
                    f"Final SOC: "
                    f"{states[-1].soc:.2f}%"
                )
            else:
                print("No route segments found.")
                print(
                    f"Final Remaining Energy: "
                    f"{remaining_energy:.2f} kWh"
                )
                print(
                    f"Final SOC: "
                    f"{starting_soc:.2f}%"
                )

        return states