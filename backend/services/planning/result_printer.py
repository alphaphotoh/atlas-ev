class ResultPrinter:

    @staticmethod
    def print(results):

        print()
        print("========== BEST TRIPS ==========")

        for result in results:

            candidate = result.candidate

            print()
            print("=" * 50)

            print(
                f"Charger: "
                f"{candidate.charger.name}"
            )

            print(
                f"Network: "
                f"{candidate.charger.network}"
            )

            print(
                f"Power: "
                f"{candidate.charger.power_kw} kW"
            )

            print(
                f"Detour: "
                f"{candidate.charger.detour_distance_km:.2f} km"
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
                f"Destination SOC: "
                f"{candidate.destination_arrival_soc:.1f}%"
            )

            print(
                f"Requires Another Stop: "
                f"{'YES' if result.requires_additional_stop else 'NO'}"
            )

            print(
                f"Charging Time: "
                f"{candidate.charging_time_minutes:.1f} min"
            )

            print(
                f"Driving Time: "
                f"{result.driving_time_minutes:.1f} min"
            )

            print(
                f"Detour Time: "
                f"{result.detour_time_minutes:.1f} min"
            )

            print(
                f"Total Trip Time: "
                f"{result.total_trip_time_minutes:.1f} min"
            )

            print(
                f"Score: "
                f"{candidate.score:.1f}"
            )