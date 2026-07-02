from backend.models.vehicles.vf9 import VF9


class RangeService:

    @staticmethod
    def estimate_range(
        battery_percent: float,
        efficiency: float
    ):

        usable_energy = VF9.usable_capacity * (battery_percent / 100)

        estimated_range = usable_energy / efficiency * 100

        return round(estimated_range, 1)