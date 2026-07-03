from backend.models.charging_candidate import ChargingCandidate

from backend.services.planning.departure_soc_service import (
    DepartureSOCService,
)
from backend.services.planning.projection_service import (
    ProjectionService,
)
from backend.services.simulation.charging_time_service import (
    ChargingTimeService,
)


class CandidateBuilder:

    @staticmethod
    def build(
        trip,
        charger,
        search_state
    ):

        projected = ProjectionService.project(
            trip.route,
            charger
        )

        remaining_distance = (
            trip.route.distance_km
            - projected.route_distance_km
        )

        departure_soc = DepartureSOCService.calculate(
            vehicle=trip.vehicle,
            remaining_distance_km=remaining_distance,
            efficiency=trip.metadata[
                "predicted_efficiency"
            ],
            planning=trip.planning
        )

        energy_added, charging_time = (
            ChargingTimeService.estimate(
                vehicle=trip.vehicle,
                arrival_soc=search_state.soc,
                target_soc=departure_soc
            )
        )

        return ChargingCandidate(

            charger=projected,

            arrival_soc=search_state.soc,

            departure_soc=departure_soc,

            charge_added_kwh=energy_added,

            charging_time_minutes=charging_time,

            total_trip_time_minutes=(
                trip.route.duration_minutes
                + charging_time
            ),

            score=0.0

        )