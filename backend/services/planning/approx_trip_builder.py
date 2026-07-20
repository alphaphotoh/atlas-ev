import math

from backend.models.route import Route
from backend.models.trip_plan import TripPlan
from backend.models.simulation_context import SimulationContext

from backend.services.simulation.energy_service import EnergyService
from backend.services.simulation.battery_service import BatteryService
from backend.services.simulation.battery_simulator import BatterySimulator


class ApproxTripBuilder:
    @staticmethod
    def build_after_charger(
        trip,
        charger,
        departure_soc
    ):
        remaining_distance_km = ApproxTripBuilder.remaining_distance_km(
            trip,
            charger
        )

        average_speed = getattr(
            trip.simulation,
            "average_speed",
            90.0,
        ) or 90.0

        duration_minutes = (
            remaining_distance_km /
            max(35.0, float(average_speed))
        ) * 60.0

        route = Route(
            distance_km=remaining_distance_km,
            duration_minutes=duration_minutes,
            geometry=ApproxTripBuilder.remaining_geometry(
                trip,
                charger
            ),
            encoded_geometry="",
            raw={
                "source": "approx_remaining_route",
                "original_distance_km": getattr(trip.route, "distance_km", None),
            },
        )

        next_trip = TripPlan(
            vehicle=trip.vehicle,
            route=route,
        )

        next_trip.planning = trip.planning
        next_trip.corridor_chargers = []
        next_trip.environment_samples = getattr(
            trip,
            "environment_samples",
            [],
        )
        next_trip.efficiency_profile = None

        next_trip.learning_vehicle_id = getattr(
            trip,
            "learning_vehicle_id",
            None,
        )

        next_trip.learning_correction_factor = getattr(
            trip,
            "learning_correction_factor",
            1.0,
        )

        predicted_efficiency = getattr(
            trip.simulation,
            "predicted_efficiency",
            0.30,
        ) or 0.30

        next_trip.base_predicted_efficiency = getattr(
            trip,
            "base_predicted_efficiency",
            predicted_efficiency,
        )

        next_trip.learned_predicted_efficiency = getattr(
            trip,
            "learned_predicted_efficiency",
            predicted_efficiency,
        )

        try:
            next_trip.battery_states = BatterySimulator.simulate(
                route=route,
                starting_soc=departure_soc,
                usable_battery_kwh=trip.vehicle.usable_battery_kwh,
                efficiency=predicted_efficiency,
                efficiency_profile=None,
            )
        except TypeError:
            next_trip.battery_states = BatterySimulator.simulate(
                route=route,
                starting_soc=departure_soc,
                usable_battery_kwh=trip.vehicle.usable_battery_kwh,
                efficiency=predicted_efficiency,
            )

        energy_needed = EnergyService.estimate_energy_needed(
            distance_km=route.distance_km,
            efficiency=predicted_efficiency,
        )

        arrival_soc = BatteryService.estimate_arrival_soc(
            starting_soc=departure_soc,
            usable_battery=trip.vehicle.usable_battery_kwh,
            energy_used=energy_needed,
        )

        next_trip.simulation = SimulationContext(
            predicted_efficiency=predicted_efficiency,
            energy_needed_kwh=energy_needed,
            arrival_soc=arrival_soc,
            average_speed=getattr(
                trip.simulation,
                "average_speed",
                average_speed,
            ),
            temperature=getattr(
                trip.simulation,
                "temperature",
                20.0,
            ),
            highway_ratio=getattr(
                trip.simulation,
                "highway_ratio",
                0.8,
            ),
        )

        next_trip.remaining_distance_km = route.distance_km
        next_trip.starting_soc = departure_soc

        return next_trip

    @staticmethod
    def remaining_distance_km(
        trip,
        charger
    ):
        route_distance_km = getattr(
            charger,
            "route_distance_km",
            None,
        )

        if route_distance_km is None:
            route_distance_km = getattr(
                charger,
                "distance_along_route_km",
                None,
            )

        if route_distance_km is None:
            route_distance_km = ApproxTripBuilder.distance_from_route_start(
                trip,
                charger,
            )

        total_distance_km = getattr(
            trip.route,
            "distance_km",
            0.0,
        ) or 0.0

        return round(
            max(
                0.0,
                total_distance_km - float(route_distance_km or 0.0),
            ),
            1,
        )

    @staticmethod
    def remaining_geometry(
        trip,
        charger
    ):
        geometry = getattr(
            trip.route,
            "geometry",
            [],
        ) or []

        charger_point = [
            getattr(charger, "longitude", 0.0),
            getattr(charger, "latitude", 0.0),
        ]

        if not geometry:
            return [
                charger_point,
            ]

        nearest_index = ApproxTripBuilder.nearest_geometry_index(
            geometry,
            charger_point,
        )

        suffix = geometry[
            nearest_index:
        ]

        if not suffix:
            suffix = [
                geometry[-1],
            ]

        return [
            charger_point,
        ] + suffix

    @staticmethod
    def nearest_geometry_index(
        geometry,
        point
    ):
        best_index = 0
        best_distance = float("inf")

        for index, candidate in enumerate(geometry):
            distance = (
                (candidate[0] - point[0]) ** 2
                + (candidate[1] - point[1]) ** 2
            )

            if distance < best_distance:
                best_distance = distance
                best_index = index

        return best_index

    @staticmethod
    def distance_from_route_start(
        trip,
        charger
    ):
        geometry = getattr(
            trip.route,
            "geometry",
            [],
        ) or []

        if not geometry:
            return 0.0

        charger_point = [
            getattr(charger, "longitude", 0.0),
            getattr(charger, "latitude", 0.0),
        ]

        nearest_index = ApproxTripBuilder.nearest_geometry_index(
            geometry,
            charger_point,
        )

        distance = 0.0

        for index in range(
            1,
            nearest_index + 1,
        ):
            distance += ApproxTripBuilder.distance_km(
                geometry[index - 1],
                geometry[index],
            )

        return distance

    @staticmethod
    def distance_km(
        point1,
        point2
    ):
        lon1, lat1 = point1
        lon2, lat2 = point2

        earth_radius_km = 6371.0

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2.0) ** 2
        )

        return earth_radius_km * 2.0 * math.atan2(
            math.sqrt(a),
            math.sqrt(1.0 - a),
        )
