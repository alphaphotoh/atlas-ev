from backend.models.vehicle import Vehicle


class EnergyPredictor:

    @staticmethod
    def estimate(
        vehicle: Vehicle,
        speed: float,
        temperature: float
    ):

        if speed < 70:
            efficiency = vehicle.default_city_efficiency

        else:
            efficiency = vehicle.default_highway_efficiency

        # Temperature adjustment
        if temperature < 0:
            efficiency += 4

        elif temperature < 10:
            efficiency += 2

        elif temperature > 30:
            efficiency += 1

        return round(efficiency, 1)