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

        projected = ProjectionService.project(

            trip.route,

            charger

        )

        arrival_state = trip.get_battery_state(

            projected.route_distance_km

        )

        print()

        print("=" * 60)

        print(f"Charger: {projected.name}")

        print(
            f"Projected route distance: "
            f"{projected.route_distance_km:.1f} km"
        )

        print(
            f"Search state distance: "
            f"{search_state.distance_km:.1f} km"
        )

        print(
            f"Detour: "
            f"{projected.detour_distance_km:.2f} km"
        )

        print(
            f"Arrival SOC: "
            f"{arrival_state.soc:.1f}%"
        )

        departure_soc = DepartureOptimizer.optimize(

            trip=trip,

            charger=projected,

            arrival_soc=arrival_state.soc

        )

        print(
            f"Departure SOC: "
            f"{departure_soc:.1f}%"
        )

        energy_added, charging_time = (

            ChargingTimeService.estimate(

                vehicle=trip.vehicle,

                charger=projected,

                arrival_soc=arrival_state.soc,

                target_soc=departure_soc

            )

        )

        print(
            f"Charge added: "
            f"{energy_added:.1f} kWh"
        )

        print(
            f"Charging time: "
            f"{charging_time:.1f} min"
        )

        return ChargingCandidate(

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

        )