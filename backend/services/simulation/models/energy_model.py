class EnergyModel:

    @staticmethod
    def energy_used(
        distance_km,
        efficiency
    ):

        return (
            distance_km *
            efficiency /
            100
        )