from backend.models.charging_candidate import ChargingCandidate

from backend.services.planning.optimizer.departure_optimizer import (
    DepartureOptimizer,
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

        # Project charger onto the route
        projected = ProjectionService.project(
            trip.route,
            charger
        )

        # Find the minimum departure SOC needed
        departure_soc = DepartureOptimizer.optimize(
            trip=trip,
            charger=projected,
            arrival_soc=search_state.soc
        )

        # Estimate charging session
        energy_added, charging_time = (
            ChargingTimeService.estimate(
                vehicle=trip.vehicle,
                arrival_soc=search_state.soc,
                target_soc=departure_soc
            )
        )

        # Build candidate
        return ChargingCandidate(

            charger=projected,

            arrival_soc=search_state.soc,

            departure_soc=departure_soc,

            charge_added_kwh=energy_added,

            charging_time_minutes=charging_time,

            total_trip_time_minutes=(
                trip.route.duration_minutes +
                charging_time
            ),

            score=0.0

        )