class ScoringService:

    @staticmethod
    def score(candidate, planning):

        score = 1000

        #
        # Prefer shorter charging sessions.
        #
        score -= (
            candidate.charging_time_minutes * 6
        )

        #
        # Prefer smaller detours.
        #
        score -= (
            candidate.charger.detour_distance_km * 20
        )

        #
        # Prefer higher-power chargers.
        #
        if candidate.charger.power_kw:

            score += min(

                candidate.charger.power_kw,

                350

            ) / 2

        #
        # Arrival SOC scoring.
        #

        arrival_soc = (
            candidate.arrival_soc
        )

        ideal_min = (
            planning.ideal_charger_arrival_soc_min
        )

        ideal_max = (
            planning.ideal_charger_arrival_soc_max
        )

        if arrival_soc < ideal_min:

            score -= (
                (ideal_min - arrival_soc) * 6
            )

        elif arrival_soc > ideal_max:

            score -= (
                (arrival_soc - ideal_max) * 4
            )

        #
        # Destination SOC.
        #

        destination_difference = abs(

            candidate.destination_arrival_soc -

            planning.target_destination_soc

        )

        score -= (
            destination_difference * 3
        )

        if (

            candidate.destination_arrival_soc <

            planning.target_destination_soc

        ):

            score -= (

                (

                    planning.target_destination_soc -

                    candidate.destination_arrival_soc

                ) * 10

            )

        return round(

            score,

            2

        )