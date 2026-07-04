from backend.models.simulation_result import SimulationResult

from backend.services.simulation.models.energy_model import EnergyModel
from backend.services.simulation.models.battery_model import BatteryModel


class TripSimulator:

    DETOUR_SPEED_KMH = 50

    @staticmethod
    def simulate(
        trip,
        candidate
    ):

        remaining_distance = (
            trip.route.distance_km -
            candidate.charger.route_distance_km
        )

        energy_used = EnergyModel.energy_used(
            remaining_distance,
            trip.simulation.predicted_efficiency
        )

        destination_soc = BatteryModel.destination_soc(
            vehicle=trip.vehicle,
            departure_soc=candidate.departure_soc,
            energy_used=energy_used
        )

        destination_soc = round(
            destination_soc,
            1
        )

        candidate.destination_arrival_soc = (
            destination_soc
        )

        requires_additional_stop = (
            destination_soc <
            trip.vehicle.min_arrival_soc
        )

        if trip.simulation.average_speed <= 0:

            driving_time = 0

        else:

            driving_time = (
                remaining_distance /
                trip.simulation.average_speed
            ) * 60

        detour_time = (
            candidate.charger.detour_distance_km /
            TripSimulator.DETOUR_SPEED_KMH
        ) * 60

        total_trip_time = (
            driving_time +
            detour_time +
            candidate.charging_time_minutes
        )

        candidate.total_trip_time_minutes = round(
            total_trip_time,
            1
        )

        return SimulationResult(

            candidate=candidate,

            destination_soc=destination_soc,

            requires_additional_stop=(
                requires_additional_stop
            ),

            energy_used_kwh=round(
                energy_used,
                1
            ),

            charging_time_minutes=round(
                candidate.charging_time_minutes,
                1
            ),

            driving_time_minutes=round(
                driving_time,
                1
            ),

            detour_time_minutes=round(
                detour_time,
                1
            ),

            total_trip_time_minutes=round(
                total_trip_time,
                1
            )

        )