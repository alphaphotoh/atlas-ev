class ScoringService:

    @staticmethod
    def score(candidate):

        score = 1000

        # Prefer shorter charging sessions
        score -= candidate.charging_time_minutes * 6

        # Prefer smaller detours
        score -= candidate.charger.detour_km * 20

        # Prefer higher charger power
        if candidate.charger.power_kw:
            score += min(
                candidate.charger.power_kw,
                350
            ) / 2

        # Prefer arriving around 10–20%
        score -= abs(
            candidate.arrival_soc - 15
        ) * 2

        return round(score, 2)