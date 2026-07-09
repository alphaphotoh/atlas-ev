class ScoringService:
    BASE_SCORE = 1000.0

    @staticmethod
    def score(candidate, planning):
        score = ScoringService.BASE_SCORE

        score -= ScoringService.charging_time_penalty(candidate)
        score -= ScoringService.detour_penalty(candidate)
        score += ScoringService.power_bonus(candidate)

        score -= ScoringService.arrival_soc_penalty(
            candidate,
            planning
        )

        score -= ScoringService.departure_soc_penalty(
            candidate,
            planning
        )

        score -= ScoringService.destination_soc_penalty(
            candidate,
            planning
        )

        score -= ScoringService.large_charge_penalty(candidate)

        return round(score, 2)

    @staticmethod
    def charging_time_penalty(candidate):
        charging_minutes = candidate.charging_time_minutes or 0.0
        return charging_minutes * 5.0

    @staticmethod
    def detour_penalty(candidate):
        detour_km = candidate.charger.detour_distance_km or 0.0
        return detour_km * 25.0

    @staticmethod
    def power_bonus(candidate):
        power_kw = candidate.charger.power_kw or 0.0
        return min(power_kw, 350.0) * 0.35

    @staticmethod
    def arrival_soc_penalty(candidate, planning):
        arrival_soc = candidate.arrival_soc or 0.0

        ideal_min = planning.ideal_charger_arrival_soc_min
        ideal_max = planning.ideal_charger_arrival_soc_max

        if ideal_min <= arrival_soc <= ideal_max:
            return 0.0

        if arrival_soc < planning.minimum_charger_arrival_soc:
            return 10000.0

        if arrival_soc < ideal_min:
            return (ideal_min - arrival_soc) * 18.0

        return (arrival_soc - ideal_max) * 8.0

    @staticmethod
    def departure_soc_penalty(candidate, planning):
        departure_soc = candidate.departure_soc or 0.0

        penalty = 0.0

        if departure_soc > 80.0:
            penalty += (departure_soc - 80.0) * 2.0

        if departure_soc > 90.0:
            penalty += (departure_soc - 90.0) * 4.0

        if departure_soc > 95.0:
            penalty += (departure_soc - 95.0) * 8.0

        if departure_soc >= planning.road_trip_charge_limit:
            penalty += 75.0

        return penalty

    @staticmethod
    def destination_soc_penalty(candidate, planning):
        destination_soc = candidate.destination_arrival_soc or 0.0
        target_soc = planning.target_destination_soc

        if destination_soc >= target_soc:
            excess_soc = destination_soc - target_soc
            return excess_soc * 2.0

        requires_additional_stop = getattr(
            candidate,
            "requires_additional_stop",
            False
        )

        destination_reachable_from_charger = getattr(
            candidate,
            "destination_reachable_from_charger",
            True
        )

        shortfall = target_soc - destination_soc

        if requires_additional_stop:
            if destination_reachable_from_charger:
                return 150.0 + (shortfall * 10.0)

            return 75.0 + min(
                shortfall * 1.5,
                60.0
            )

        return 300.0 + (shortfall * 20.0)

    @staticmethod
    def large_charge_penalty(candidate):
        arrival_soc = candidate.arrival_soc or 0.0
        departure_soc = candidate.departure_soc or 0.0

        soc_added = max(
            departure_soc - arrival_soc,
            0.0
        )

        penalty = 0.0

        if soc_added > 60.0:
            penalty += (soc_added - 60.0) * 2.0

        if soc_added > 80.0:
            penalty += (soc_added - 80.0) * 5.0

        return penalty