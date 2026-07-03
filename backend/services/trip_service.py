from backend.models.registry import VehicleRegistry
from backend.models.trip_plan import TripPlan

from backend.services.adapters.geocoding_service import GeocodingService
from backend.services.adapters.routing_service import RoutingService

from backend.services.simulation.energy_service import EnergyService
from backend.services.simulation.battery_service import BatteryService
from backend.services.simulation.battery_simulator import BatterySimulator

from backend.services.planning.charging_planner import ChargingPlanner


class TripService:

    @staticmethod
    async def build_trip(
        vehicle_id: str,
        origin: str,
        destination: str,
        starting_soc: float,
        temperature: float,
        average_speed: float,
        highway_ratio: float
    ):

        vehicle = VehicleRegistry.get(vehicle_id)

        origin_data = await GeocodingService.search(origin)
        destination_data = await GeocodingService.search(destination)

        origin_coords = origin_data["features"][0]["geometry"]["coordinates"]
        destination_coords = destination_data["features"][0]["geometry"]["coordinates"]

        route = await RoutingService.get_route(
            origin_coords,
            destination_coords
        )

        trip = TripPlan(
            vehicle=vehicle,
            route=route
        )

        print(f"Route points: {len(trip.route.geometry)}")
        print(f"Route segments: {len(trip.route.segments)}")

        predicted_efficiency = EnergyService.predict_efficiency(
            temperature=temperature,
            average_speed=average_speed,
            highway_ratio=highway_ratio
        )

        trip.battery_states = BatterySimulator.simulate(
            trip.route,
            starting_soc,
            vehicle.usable_battery_kwh,
            predicted_efficiency
        )

        print(
            f"Battery simulation points: {len(trip.battery_states)}"
        )

        print(
            f"Final SOC: {trip.battery_states[-1].soc:.1f}%"
        )

        energy_needed = EnergyService.estimate_energy_needed(
            distance_km=trip.route.distance_km,
            efficiency=predicted_efficiency
        )

        arrival_soc = BatteryService.estimate_arrival_soc(
            starting_soc=starting_soc,
            usable_battery=vehicle.usable_battery_kwh,
            energy_used=energy_needed
        )

        trip.metadata["predicted_efficiency"] = predicted_efficiency
        trip.metadata["energy_needed_kwh"] = energy_needed
        trip.metadata["arrival_soc"] = arrival_soc

        trip.recommended_chargers = await ChargingPlanner.plan(
            trip
        )

        return {
            "vehicle": trip.vehicle.name,
            "origin": origin,
            "destination": destination,
            "distance_km": round(trip.route.distance_km, 1),
            "duration_minutes": round(trip.route.duration_minutes),
            "predicted_efficiency": round(
                trip.metadata["predicted_efficiency"], 1
            ),
            "energy_needed_kwh": round(
                trip.metadata["energy_needed_kwh"], 1
            ),
            "estimated_arrival_soc": round(
                trip.metadata["arrival_soc"], 1
            ),
            "charging_required": (
                trip.metadata["arrival_soc"]
                < trip.vehicle.min_arrival_soc
            ),
            "charging_plan": trip.recommended_chargers
        }