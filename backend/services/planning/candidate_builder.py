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
    async def build(
        trip,
        charger
    ):

        projected = ProjectionService.project(

            trip.route,

            charger

        )

        arrival_state = trip.get_battery_state(

            projected.route_distance_km

        )

        departure_soc, next_trip = await DepartureOptimizer.optimize(

            trip=trip,

            charger=projected,

            arrival_soc=arrival_state.soc

        )

        energy_added, charging_time = (

            ChargingTimeService.estimate(

                vehicle=trip.vehicle,

                charger=projected,

                arrival_soc=arrival_state.soc,

                target_soc=departure_soc

            )

        )

        return (

            ChargingCandidate(

                charger=projected,

                battery_state=arrival_state,

                arrival_soc=arrival_state.soc,

                departure_soc=departure_soc,

                destination_arrival_soc=0.0,

                charge_added_kwh=energy_added,

                charging_time_minutes=charging_time,

                total_trip_time_minutes=(

                    trip.route.duration_minutes +

                    charging_time

                ),

                score=0.0

            ),

            next_trip

        )