from backend.models.trip_plan import TripPlan
from backend.models.simulation_context import SimulationContext

from backend.services.adapters.geocoding_service import GeocodingService
from backend.services.adapters.routing_service import RoutingService
from backend.services.adapters.weather_service import WeatherService

from backend.services.learning.learning_service import LearningService

from backend.services.planning.route_cache import RouteCache
from backend.services.planning.route_weather_service import RouteWeatherService

from backend.services.simulation.energy_service import EnergyService
from backend.services.simulation.battery_service import BatteryService
from backend.services.simulation.battery_simulator import BatterySimulator
from backend.services.simulation.efficiency_profile_service import (
    EfficiencyProfileService,
)


class TripBuilder:
    MIN_LEARNING_CORRECTION_FACTOR = 0.75
    MAX_LEARNING_CORRECTION_FACTOR = 1.35

    @staticmethod
    async def build_trip(
        vehicle,
        origin,
        destination,
        starting_soc,
        average_speed,
        highway_ratio
    ):
        origin_data = await GeocodingService.search(
            origin
        )

        destination_data = await GeocodingService.search(
            destination
        )

        origin_coords = (
            origin_data["features"][0]["geometry"]["coordinates"]
        )

        destination_coords = (
            destination_data["features"][0]["geometry"]["coordinates"]
        )

        route = await RoutingService.get_route(
            origin_coords,
            destination_coords
        )

        return await TripBuilder.build_from_route(
            vehicle=vehicle,
            route=route,
            origin_coords=origin_coords,
            starting_soc=starting_soc,
            average_speed=average_speed,
            highway_ratio=highway_ratio
        )

    @staticmethod
    async def build_trip_via_points(
        vehicle,
        origin,
        waypoints,
        destination,
        starting_soc,
        average_speed,
        highway_ratio
    ):
        origin_data = await GeocodingService.search(
            origin
        )

        destination_data = await GeocodingService.search(
            destination
        )

        origin_coords = (
            origin_data["features"][0]["geometry"]["coordinates"]
        )

        destination_coords = (
            destination_data["features"][0]["geometry"]["coordinates"]
        )

        waypoint_coordinates = []

        for waypoint in waypoints:
            waypoint_data = await GeocodingService.search(
                waypoint
            )

            waypoint_coordinates.append(
                waypoint_data["features"][0]["geometry"]["coordinates"]
            )

        route = await RoutingService.get_route_via_waypoints(
            start=origin_coords,
            waypoint_coordinates=waypoint_coordinates,
            end=destination_coords
        )

        return await TripBuilder.build_from_route(
            vehicle=vehicle,
            route=route,
            origin_coords=origin_coords,
            starting_soc=starting_soc,
            average_speed=average_speed,
            highway_ratio=highway_ratio
        )

    @staticmethod
    async def build_from_route(
        vehicle,
        route,
        origin_coords,
        starting_soc,
        average_speed,
        highway_ratio
    ):
        weather = await WeatherService.get_weather(
            latitude=origin_coords[1],
            longitude=origin_coords[0]
        )

        trip = TripPlan(
            vehicle=vehicle,
            route=route
        )

        trip.environment_samples = await RouteWeatherService.sample(
            route
        )

        base_predicted_efficiency = EnergyService.predict_efficiency(
            temperature=weather.temperature_c,
            average_speed=average_speed,
            highway_ratio=highway_ratio
        )

        learning_correction_factor = (
            TripBuilder.get_learning_correction_factor(
                vehicle
            )
        )

        predicted_efficiency = (
            base_predicted_efficiency *
            learning_correction_factor
        )

        trip.efficiency_profile = EfficiencyProfileService.build(
            route=route,
            environment_samples=trip.environment_samples,
            base_efficiency=predicted_efficiency
        )

        trip.battery_states = BatterySimulator.simulate(
            route=route,
            starting_soc=starting_soc,
            usable_battery_kwh=vehicle.usable_battery_kwh,
            efficiency=predicted_efficiency,
            efficiency_profile=trip.efficiency_profile
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

        trip.simulation = SimulationContext(
            predicted_efficiency=predicted_efficiency,
            energy_needed_kwh=energy_needed,
            arrival_soc=arrival_soc,
            average_speed=average_speed,
            temperature=weather.temperature_c,
            highway_ratio=highway_ratio
        )

        trip.remaining_distance_km = route.distance_km
        trip.starting_soc = starting_soc

        trip.learning_vehicle_id = TripBuilder.resolve_learning_vehicle_id(
            vehicle
        )

        trip.learning_correction_factor = learning_correction_factor
        trip.base_predicted_efficiency = base_predicted_efficiency
        trip.learned_predicted_efficiency = predicted_efficiency

        return trip

    @staticmethod
    async def build(
        trip,
        charger,
        departure_soc
    ):
        route = await TripBuilder.build_route(
            trip,
            charger
        )

        next_trip = TripPlan(
            vehicle=trip.vehicle,
            route=route
        )

        next_trip.planning = trip.planning
        next_trip.corridor_chargers = trip.corridor_chargers
        next_trip.environment_samples = trip.environment_samples
        next_trip.efficiency_profile = trip.efficiency_profile

        next_trip.learning_vehicle_id = getattr(
            trip,
            "learning_vehicle_id",
            None
        )

        next_trip.learning_correction_factor = getattr(
            trip,
            "learning_correction_factor",
            1.0
        )

        next_trip.base_predicted_efficiency = getattr(
            trip,
            "base_predicted_efficiency",
            trip.simulation.predicted_efficiency
        )

        next_trip.learned_predicted_efficiency = getattr(
            trip,
            "learned_predicted_efficiency",
            trip.simulation.predicted_efficiency
        )

        next_trip.battery_states = BatterySimulator.simulate(
            route=route,
            starting_soc=departure_soc,
            usable_battery_kwh=trip.vehicle.usable_battery_kwh,
            efficiency=trip.simulation.predicted_efficiency,
            efficiency_profile=trip.efficiency_profile
        )

        energy_needed = EnergyService.estimate_energy_needed(
            distance_km=route.distance_km,
            efficiency=trip.simulation.predicted_efficiency
        )

        arrival_soc = BatteryService.estimate_arrival_soc(
            starting_soc=departure_soc,
            usable_battery=trip.vehicle.usable_battery_kwh,
            energy_used=energy_needed
        )

        next_trip.simulation = SimulationContext(
            predicted_efficiency=trip.simulation.predicted_efficiency,
            energy_needed_kwh=energy_needed,
            arrival_soc=arrival_soc,
            average_speed=trip.simulation.average_speed,
            temperature=trip.simulation.temperature,
            highway_ratio=trip.simulation.highway_ratio
        )

        next_trip.remaining_distance_km = route.distance_km
        next_trip.starting_soc = departure_soc

        return next_trip

    @staticmethod
    async def build_route(
        trip,
        charger
    ):
        start = [
            charger.longitude,
            charger.latitude
        ]

        destination = trip.route.geometry[-1]

        cached = RouteCache.get(
            start,
            destination
        )

        if cached is not None:
            return cached

        route = await RoutingService.get_route(
            start,
            destination
        )

        RouteCache.set(
            start,
            destination,
            route
        )

        return route

    @staticmethod
    def get_learning_correction_factor(vehicle):
        vehicle_id = TripBuilder.resolve_learning_vehicle_id(
            vehicle
        )

        if vehicle_id is None:
            return 1.0

        profile = LearningService.get_profile(
            vehicle_id=vehicle_id
        )

        correction_factor = profile.get(
            "correction_factor",
            1.0
        )

        return TripBuilder.safe_correction_factor(
            correction_factor
        )

    @staticmethod
    def resolve_learning_vehicle_id(vehicle):
        vehicle_id = getattr(
            vehicle,
            "vehicle_id",
            None
        )

        if vehicle_id:
            return vehicle_id

        vehicle_id = getattr(
            vehicle,
            "id",
            None
        )

        if vehicle_id:
            return vehicle_id

        name = (
            getattr(
                vehicle,
                "name",
                ""
            ) or ""
        ).lower()

        if "vf9" in name or "vinfast" in name:
            return "vf9"

        return None

    @staticmethod
    def safe_correction_factor(value):
        try:
            correction_factor = float(
                value
            )
        except (TypeError, ValueError):
            return 1.0

        if correction_factor <= 0:
            return 1.0

        if correction_factor < TripBuilder.MIN_LEARNING_CORRECTION_FACTOR:
            return TripBuilder.MIN_LEARNING_CORRECTION_FACTOR

        if correction_factor > TripBuilder.MAX_LEARNING_CORRECTION_FACTOR:
            return TripBuilder.MAX_LEARNING_CORRECTION_FACTOR

        return correction_factor