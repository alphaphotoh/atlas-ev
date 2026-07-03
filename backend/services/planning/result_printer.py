class ResultPrinter:

    @staticmethod
    def print(results):

        print()
        print("========== BEST TRIPS ==========")

        for result in results:

            candidate = result.candidate

            print()

            print(candidate.charger.name)

            print(
                f"Total Time: "
                f"{result.total_trip_time_minutes:.1f} min"
            )

            print(
                f"Driving: "
                f"{result.driving_time_minutes:.1f} min"
            )

            print(
                f"Charging: "
                f"{result.charging_time_minutes:.1f} min"
            )

            print(
                f"Detour: "
                f"{result.detour_time_minutes:.1f} min"
            )

            print(
                f"Destination SOC: "
                f"{result.destination_soc:.1f}%"
            )