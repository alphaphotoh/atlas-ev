from backend.models.vehicles.vf9 import VF9
from backend.services.energy import EnergyPredictor


class TripPlanner:

    @staticmethod
    def estimate_arrival_soc(
        battery_percent: float,
        trip_distance_km: float,
        average_speed: float,
        outside_temperature: float
    ):

        efficiency = EnergyPredictor.estimate(
            vehicle=VF9,
            speed=average_speed,
            temperature=outside_temperature
        )

        energy_used = trip_distance_km * efficiency / 100

        remaining_energy = (
            VF9.usable_capacity *
            battery_percent / 100
        ) - energy_used

        remaining_soc = (
            remaining_energy /
            VF9.usable_capacity
        ) * 100

        return {
            "efficiency": round(efficiency, 1),
            "energy_used": round(energy_used, 1),
            "arrival_soc": round(remaining_soc, 1)
        }