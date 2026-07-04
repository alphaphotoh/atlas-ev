class ScoringService:

    IDEAL_CHARGER_ARRIVAL_SOC = 27.5
    IDEAL_DESTINATION_SOC = 25.0

    @staticmethod
    def score(candidate):

        score = 1000

        # Prefer shorter charging sessions
        score -= candidate.charging_time_minutes * 6

        # Prefer smaller detours
        score -= (
            candidate.charger.detour_distance_km * 20
        )

        # Prefer higher-power chargers
        if candidate.charger.power_kw:

            score += min(
                candidate.charger.power_kw,
                350
            ) / 2

        # Strongly prefer arriving at chargers around 25-30%
        arrival_difference = abs(
            candidate.arrival_soc -
            ScoringService.IDEAL_CHARGER_ARRIVAL_SOC
        )

        score -= arrival_difference * 8

        # Heavy penalty for arriving below 25%
        if candidate.arrival_soc < 25:

            score -= (
                (25 - candidate.arrival_soc) * 15
            )

        # Prefer arriving at destination around 25%
        destination_difference = abs(
            candidate.destination_arrival_soc -
            ScoringService.IDEAL_DESTINATION_SOC
        )

        score -= destination_difference * 4

        # Heavy penalty if destination SOC is below 25%
        if candidate.destination_arrival_soc < 25:

            score -= (
                (25 - candidate.destination_arrival_soc) * 20
            )

        return round(
            score,
            2
        )