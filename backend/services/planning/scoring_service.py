class ScoringService:

    @staticmethod
    def score(charger):

        score = 0

        if charger.supports_vf9:
            score += 100

        power = charger.power_kw or 0

        if power >= 250:
            score += 50

        elif power >= 150:
            score += 40

        elif power >= 100:
            score += 30

        elif power >= 50:
            score += 20

        elif power >= 22:
            score += 10

        distance = charger.distance_km or 999

        if distance <= 2:
            score += 30

        elif distance <= 5:
            score += 20

        elif distance <= 10:
            score += 10

        charger.score = score

        return charger