from types import SimpleNamespace

from backend.models.charging_candidate import ChargingCandidate

from backend.services.planning.projection_service import ProjectionService
from backend.services.simulation.battery_service import BatteryService
from backend.services.simulation.energy_service import EnergyService


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

        arrival_state = CandidateBuilder.get_arrival_state(
            trip=trip,
            route_distance_km=projected.route_distance_km
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

    @staticmethod
    def get_arrival_state(
        trip,
        route_distance_km
    ):
        try:
            if getattr(trip, "battery_states", None):
                return trip.get_battery_state(
                    route_distance_km
                )

        except ValueError:
            pass

        except RuntimeError:
            pass

        return CandidateBuilder.estimate_arrival_state(
            trip=trip,
            route_distance_km=route_distance_km
        )

    @staticmethod
    def estimate_arrival_state(
        trip,
        route_distance_km
    ):
        route_distance_km = CandidateBuilder.safe_route_distance(
            trip=trip,
            route_distance_km=route_distance_km
        )

        predicted_efficiency = CandidateBuilder.predicted_efficiency(
            trip
        )

        energy_used_kwh = EnergyService.estimate_energy_needed(
            distance_km=route_distance_km,
            efficiency=predicted_efficiency
        )

        starting_soc = getattr(
            trip,
            "starting_soc",
            0.0
        )

        usable_battery_kwh = trip.vehicle.usable_battery_kwh

        arrival_soc = BatteryService.estimate_arrival_soc(
            starting_soc=starting_soc,
            usable_battery=usable_battery_kwh,
            energy_used=energy_used_kwh
        )

        return SimpleNamespace(
            route_distance_km=route_distance_km,
            distance_km=route_distance_km,
            energy_used_kwh=energy_used_kwh,
            soc=arrival_soc
        )

    @staticmethod
    def predicted_efficiency(trip):
        if trip.simulation is not None:
            return trip.simulation.predicted_efficiency

        return 31.0

    @staticmethod
    def safe_route_distance(
        trip,
        route_distance_km
    ):
        value = route_distance_km or 0.0

        if value < 0:
            return 0.0

        route = getattr(
            trip,
            "route",
            None
        )

        route_distance = getattr(
            route,
            "distance_km",
            None
        )

        if route_distance is None:
            return value

        if value > route_distance:
            return route_distance

        return value