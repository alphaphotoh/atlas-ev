class EnergyService:

    @staticmethod
    def predict_efficiency(
        temperature: float,
        average_speed: float,
        highway_ratio: float
    ):

        efficiency = 27.0

        # Highway penalty
        efficiency += highway_ratio * 4

        # Speed penalty
        if average_speed > 100:
            efficiency += (average_speed - 100) * 0.15

        # Cold weather penalty
        if temperature < 15:
            efficiency += (15 - temperature) * 0.25

        # Hot weather A/C penalty
        elif temperature > 30:
            efficiency += (temperature - 30) * 0.10

        return round(efficiency, 1)

    @staticmethod
    def estimate_energy_needed(
        distance_km: float,
        efficiency: float
    ):
        return distance_km * efficiency / 100