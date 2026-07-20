from backend.services.simulation.route_speed_service import RouteSpeedService
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
from backend.services.simulation.trip_conditions_service import (
    TripConditionsService,
)
from backend.services.simulation.traffic_impact_service import (
    TrafficImpactService,
)
from backend.services.adapters.live_traffic_service import (
    LiveTrafficService,
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
        highway_ratio,
        traffic_mode="live",
        traffic_level=None,
        trip_conditions=None
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
            highway_ratio=highway_ratio,
            traffic_mode=traffic_mode,
            traffic_level=traffic_level,
            trip_conditions=trip_conditions
        )

    @staticmethod
    async def build_trip_via_points(
        vehicle,
        origin,
        waypoints,
        destination,
        starting_soc,
        average_speed,
        highway_ratio,
        traffic_mode="live",
        traffic_level=None,
        trip_conditions=None
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
            highway_ratio=highway_ratio,
            traffic_mode=traffic_mode,
            traffic_level=traffic_level,
            trip_conditions=trip_conditions
        )

    @staticmethod
    async def build_from_route(
        vehicle,
        route,
        origin_coords,
        starting_soc,
        average_speed,
        highway_ratio,
        traffic_mode="live",
        traffic_level=None,
        trip_conditions=None
    ):
        speed_estimate = RouteSpeedService.estimate(
            route=route,
            fallback_average_speed_kmh=average_speed,
        )
        average_speed = speed_estimate.average_speed_kmh

        try:
            setattr(route, "speed_estimate", speed_estimate)
        except Exception:
            pass

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

        learned_predicted_efficiency = (
            base_predicted_efficiency *
            learning_correction_factor
        )

        trip_conditions_impact = TripConditionsService.build(
            conditions=trip_conditions,
            distance_km=route.distance_km,
            usable_battery_kwh=vehicle.usable_battery_kwh
        )

        conditions_adjusted_efficiency = (
            learned_predicted_efficiency +
            trip_conditions_impact.efficiency_adjustment_kwh_per_100km
        )

        simulation_usable_battery_kwh = (
            trip_conditions_impact.effective_usable_battery_kwh
            or vehicle.usable_battery_kwh
        )

        live_traffic_result = None

        if traffic_mode == "live":
            live_traffic_result = await LiveTrafficService.get_live_traffic_for_route(
                route
            )

        if live_traffic_result is not None:
            traffic_impact = TrafficImpactService.build_from_live_result(
                traffic_mode=traffic_mode,
                distance_km=route.distance_km,
                duration_minutes=route.duration_minutes,
                highway_ratio=highway_ratio,
                usable_battery_kwh=simulation_usable_battery_kwh,
                live_result=live_traffic_result
            )

        else:
            traffic_impact = TrafficImpactService.build(
                traffic_mode=traffic_mode,
                traffic_level=traffic_level,
                distance_km=route.distance_km,
                duration_minutes=route.duration_minutes,
                highway_ratio=highway_ratio,
                usable_battery_kwh=simulation_usable_battery_kwh
            )

        if traffic_impact.applied and traffic_impact.adjusted_duration_minutes:
            route.duration_minutes = traffic_impact.adjusted_duration_minutes

        traffic_adjusted_efficiency = (
            conditions_adjusted_efficiency +
            traffic_impact.efficiency_adjustment_kwh_per_100km
        )

        trip.efficiency_profile = EfficiencyProfileService.build(
            route=route,
            environment_samples=trip.environment_samples,
            base_efficiency=traffic_adjusted_efficiency
        )

        trip.battery_states = BatterySimulator.simulate(
            route=route,
            starting_soc=starting_soc,
            usable_battery_kwh=simulation_usable_battery_kwh,
            efficiency=traffic_adjusted_efficiency,
            efficiency_profile=trip.efficiency_profile
        )

        trip.simulation = TripBuilder.build_simulation_context(
            route=route,
            battery_states=trip.battery_states,
            fallback_efficiency=traffic_adjusted_efficiency,
            average_speed=average_speed,
            temperature=weather.temperature_c,
            highway_ratio=highway_ratio,
            starting_soc=starting_soc,
            usable_battery_kwh=simulation_usable_battery_kwh
        )

        trip.remaining_distance_km = route.distance_km
        trip.starting_soc = starting_soc

        trip.learning_vehicle_id = TripBuilder.resolve_learning_vehicle_id(
            vehicle
        )

        trip.learning_correction_factor = learning_correction_factor
        trip.base_predicted_efficiency = base_predicted_efficiency
        trip.learned_predicted_efficiency = learned_predicted_efficiency
        trip.trip_conditions = trip_conditions
        trip.trip_conditions_impact = trip_conditions_impact
        trip.traffic_mode = traffic_mode
        trip.traffic_level = traffic_level
        trip.traffic_impact = traffic_impact
        trip.traffic_adjusted_efficiency = traffic_adjusted_efficiency
        trip.conditions_adjusted_efficiency = conditions_adjusted_efficiency
        trip.effective_usable_battery_kwh = simulation_usable_battery_kwh

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
        next_trip.trip_conditions = getattr(
            trip,
            "trip_conditions",
            None
        )
        next_trip.trip_conditions_impact = getattr(
            trip,
            "trip_conditions_impact",
            None
        )
        next_trip.traffic_impact = getattr(
            trip,
            "traffic_impact",
            None
        )
        next_trip.conditions_adjusted_efficiency = getattr(
            trip,
            "conditions_adjusted_efficiency",
            trip.simulation.predicted_efficiency
        )
        next_trip.effective_usable_battery_kwh = TripBuilder.effective_usable_battery_kwh(
            trip
        )

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
            usable_battery_kwh=TripBuilder.effective_usable_battery_kwh(
                trip
            ),
            efficiency=trip.simulation.predicted_efficiency,
            efficiency_profile=trip.efficiency_profile
        )

        next_trip.simulation = TripBuilder.build_simulation_context(
            route=route,
            battery_states=next_trip.battery_states,
            fallback_efficiency=trip.simulation.predicted_efficiency,
            average_speed=trip.simulation.average_speed,
            temperature=trip.simulation.temperature,
            highway_ratio=trip.simulation.highway_ratio,
            starting_soc=departure_soc,
            usable_battery_kwh=TripBuilder.effective_usable_battery_kwh(
                trip
            )
        )

        next_trip.remaining_distance_km = route.distance_km
        next_trip.starting_soc = departure_soc

        return next_trip

    @staticmethod
    def build_simulation_context(
        route,
        battery_states,
        fallback_efficiency,
        average_speed,
        temperature,
        highway_ratio,
        starting_soc,
        usable_battery_kwh
    ):
        if battery_states:
            energy_needed = TripBuilder.energy_used_from_battery_states(
                battery_states=battery_states
            )

            arrival_soc = TripBuilder.arrival_soc_from_battery_states(
                battery_states=battery_states
            )

            predicted_efficiency = TripBuilder.effective_efficiency_from_battery_states(
                battery_states=battery_states,
                route_distance_km=route.distance_km,
                fallback_efficiency=fallback_efficiency
            )

        else:
            energy_needed = EnergyService.estimate_energy_needed(
                distance_km=route.distance_km,
                efficiency=fallback_efficiency
            )

            arrival_soc = BatteryService.estimate_arrival_soc(
                starting_soc=starting_soc,
                usable_battery=usable_battery_kwh,
                energy_used=energy_needed
            )

            predicted_efficiency = fallback_efficiency

        return SimulationContext(
            predicted_efficiency=predicted_efficiency,
            energy_needed_kwh=round(
                energy_needed,
                3
            ),
            arrival_soc=round(
                arrival_soc,
                3
            ),
            average_speed=average_speed,
            temperature=temperature,
            highway_ratio=highway_ratio
        )

    @staticmethod
    def energy_used_from_battery_states(
        battery_states
    ):
        if not battery_states:
            return 0.0

        energy_used = sum(
            getattr(
                state,
                "energy_used_kwh",
                0.0
            ) or 0.0
            for state in battery_states
        )

        return round(
            energy_used,
            3
        )

    @staticmethod
    def arrival_soc_from_battery_states(
        battery_states
    ):
        if not battery_states:
            return 0.0

        return round(
            battery_states[-1].soc,
            3
        )

    @staticmethod
    def effective_efficiency_from_battery_states(
        battery_states,
        route_distance_km,
        fallback_efficiency
    ):
        if not battery_states:
            return fallback_efficiency

        if not route_distance_km:
            return fallback_efficiency

        if route_distance_km <= 0:
            return fallback_efficiency

        energy_used = TripBuilder.energy_used_from_battery_states(
            battery_states=battery_states
        )

        efficiency = (
            energy_used /
            route_distance_km
        ) * 100

        return round(
            efficiency,
            3
        )


    @staticmethod
    def effective_usable_battery_kwh(trip):
        value = getattr(
            trip,
            "effective_usable_battery_kwh",
            None
        )

        if value:
            return value

        vehicle = getattr(
            trip,
            "vehicle",
            None
        )

        return getattr(
            vehicle,
            "usable_battery_kwh",
            0.0
        )

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