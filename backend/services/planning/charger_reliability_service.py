class ChargerReliabilityService:
    NETWORK_SCORES = {
        "tesla": 0.92,
        "petro-canada": 0.84,
        "petro canada": 0.84,
        "ivy": 0.82,
        "flo": 0.80,
        "chargepoint": 0.78,
        "electrify america": 0.76,
        "shell": 0.75,
        "evgo": 0.74,
        "red e": 0.72,
        "ev connect": 0.70
    }

    DEFAULT_NETWORK_SCORE = 0.68

    @staticmethod
    def score_charger(charger):
        network = (
            getattr(
                charger,
                "network",
                ""
            ) or ""
        )

        power_kw = getattr(
            charger,
            "power_kw",
            None
        )

        detour_km = (
            getattr(
                charger,
                "detour_distance_km",
                0.0
            ) or 0.0
        )

        network_score = ChargerReliabilityService.network_score(
            network
        )

        power_score = ChargerReliabilityService.power_score(
            power_kw
        )

        detour_score = ChargerReliabilityService.detour_score(
            detour_km
        )

        score = (
            (network_score * 0.45) +
            (power_score * 0.35) +
            (detour_score * 0.20)
        )

        score = max(
            0.0,
            min(
                1.0,
                score
            )
        )

        reliability_score = round(
            score * 100,
            1
        )

        return {
            "reliability_score": reliability_score,
            "reliability_label": ChargerReliabilityService.label(
                reliability_score
            ),
            "availability_status": "unknown",
            "is_live_availability": False,
            "reliability_notes": ChargerReliabilityService.notes(
                network=network,
                power_kw=power_kw,
                detour_km=detour_km,
                reliability_score=reliability_score
            )
        }

    @staticmethod
    def network_score(network):
        normalized = (
            network or ""
        ).lower()

        for key, score in ChargerReliabilityService.NETWORK_SCORES.items():
            if key.lower() in normalized:
                return score

        return ChargerReliabilityService.DEFAULT_NETWORK_SCORE

    @staticmethod
    def power_score(power_kw):
        if power_kw is None:
            return 0.55

        try:
            power = float(
                power_kw
            )
        except (TypeError, ValueError):
            return 0.55

        if power >= 300:
            return 0.95

        if power >= 200:
            return 0.88

        if power >= 150:
            return 0.80

        if power >= 100:
            return 0.70

        if power >= 50:
            return 0.55

        return 0.40

    @staticmethod
    def detour_score(detour_km):
        try:
            detour = float(
                detour_km
            )
        except (TypeError, ValueError):
            return 0.60

        if detour <= 0.5:
            return 0.95

        if detour <= 1.5:
            return 0.85

        if detour <= 3.0:
            return 0.72

        if detour <= 5.0:
            return 0.58

        return 0.40

    @staticmethod
    def label(score):
        if score >= 85:
            return "High"

        if score >= 70:
            return "Medium"

        return "Low"

    @staticmethod
    def notes(
        network,
        power_kw,
        detour_km,
        reliability_score
    ):
        notes = []

        if network:
            notes.append(
                f"Network reputation included: {network}."
            )
        else:
            notes.append(
                "Network is unknown, so reliability score is conservative."
            )

        if power_kw is None:
            notes.append(
                "Charger power is unknown."
            )
        elif power_kw >= 200:
            notes.append(
                "High-power charger improves confidence."
            )
        elif power_kw < 100:
            notes.append(
                "Lower charger power may increase stop time."
            )

        if detour_km <= 0.5:
            notes.append(
                "Very small detour from route."
            )
        elif detour_km >= 3:
            notes.append(
                "Longer detour reduces backup confidence."
            )

        notes.append(
            "Live stall availability is not connected yet."
        )

        if reliability_score < 70:
            notes.append(
                "Use a backup charger if possible."
            )

        return notes