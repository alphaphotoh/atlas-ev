from backend.models.charging_candidate import ChargingCandidate

from backend.services.planning.projection_service import (
    ProjectionService,
)


class CandidateBuilder:

    @staticmethod
    def build(
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

        return ChargingCandidate(

            charger=projected,

            battery_state=arrival_state,

            arrival_soc=arrival_state.soc,

            departure_soc=arrival_state.soc,

            destination_arrival_soc=0.0,

            charge_added_kwh=0.0,

            charging_time_minutes=0.0,

            total_trip_time_minutes=0.0,

            score=0.0

        )