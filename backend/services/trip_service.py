from backend.models.registry import VehicleRegistry
from backend.services.battery_service import BatteryService
from backend.services.battery_simulator import BatterySimulator
from backend.services.charging_planner import ChargingPlanner
from backend.services.energy_service import EnergyService
from backend.services.geocoding_service import GeocodingService
from backend.services.routing_service import RoutingService


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

        print(f"Route points: {len(route.geometry)}")
        print(f"Route segments: {len(route.segments)}")

        predicted_efficiency = EnergyService.predict_efficiency(
            temperature=temperature,
            average_speed=average_speed,
            highway_ratio=highway_ratio
        )

        battery_states = BatterySimulator.simulate(
            route,
            starting_soc,
            vehicle.usable_battery_kwh,
            predicted_efficiency
        )

        print(
            f"Battery simulation points: {len(battery_states)}"
        )

        print(
            f"Final SOC: {battery_states[-1].soc:.1f}%"
        )

        charging_plan = await ChargingPlanner.plan(
            route,
            battery_states
        )

        energy_needed = EnergyService.estimate_energy_needed(
            distance_km=route.distance_km,
            efficiency=predicted_efficiency
        )

        arrival_soc = BatteryService.estimate_arrival_soc(
            starting_soc=starting_soc,
            usable_battery=vehicle.usable_battery_kwh,
            energy_used=energy_needed
        )

        return {
            "vehicle": vehicle.name,
            "origin": origin,
            "destination": destination,
            "distance_km": round(route.distance_km, 1),
            "duration_minutes": round(route.duration_minutes),
            "predicted_efficiency": predicted_efficiency,
            "energy_needed_kwh": round(energy_needed, 1),
            "estimated_arrival_soc": round(arrival_soc, 1),
            "charging_required": arrival_soc < vehicle.min_arrival_soc,
            "charging_plan": charging_plan
        }