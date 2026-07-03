class EnergyModel:

    @staticmethod
    def energy_used(
        distance_km: float,
        efficiency: float
    ) -> float:

        return (
            distance_km *
            efficiency /
            100
        )