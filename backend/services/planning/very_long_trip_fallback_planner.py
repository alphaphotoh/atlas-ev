import copy
import math
from types import SimpleNamespace

from backend.models.trip_node import TripNode
from backend.models.trip_itinerary import TripItinerary
from backend.models.trip_leg import TripLeg
from backend.models.trip_planning_result import TripPlanningResult

from backend.services.planning.corridor_service import CorridorService
from backend.services.planning.planner_logger import PlannerLogger
from backend.services.simulation.charging_time_service import ChargingTimeService


class VeryLongTripFallbackPlanner:
    MAX_STOPS = 12
    MIN_ARRIVAL_SOC = 5.0
    PREFERRED_MIN_ARRIVAL_SOC = 10.0
    LOW_SOC_RESCUE_MIN_ARRIVAL_SOC = 2.0
    INTERMEDIATE_TARGET_SOC = 98.0
    SPARSE_FINAL_ZONE_KM = 650.0
    INTERMEDIATE_TARGET_SOC = 98.0
    SPARSE_FINAL_ZONE_KM = 650.0
    TARGET_CHARGER_ARRIVAL_SOC = 16.0
    LONG_ROUTE_THRESHOLD_KM = 1000.0

    @staticmethod
    async def plan(trip):
        route_distance = VeryLongTripFallbackPlanner.route_distance_km(trip)

        if route_distance < VeryLongTripFallbackPlanner.LONG_ROUTE_THRESHOLD_KM:
            return None

        PlannerLogger.log()
        PlannerLogger.log("========== VERY LONG TRIP FALLBACK ==========")
        PlannerLogger.log(f"Initial route distance: {route_distance:.1f} km")

        itinerary = TripItinerary()
        current_trip = trip
        parent = None
        visited = set()
        completed_node = None

        for depth in range(VeryLongTripFallbackPlanner.MAX_STOPS):
            if VeryLongTripFallbackPlanner.is_complete(current_trip):
                completed_node = TripNode(
                    trip=current_trip,
                    itinerary=itinerary,
                    depth=depth,
                    parent=parent,
                    visited_chargers=visited,
                    g_cost=0.0,
                    h_cost=0.0,
                )
                break

            candidate = await VeryLongTripFallbackPlanner.best_candidate(
                current_trip=current_trip,
                visited=visited,
            )

            if candidate is None:
                PlannerLogger.log("Fallback planner found no usable charger.")
                break

            departure_soc = VeryLongTripFallbackPlanner.departure_soc_for_candidate(
                current_trip,
                candidate,
            )

            next_trip = VeryLongTripFallbackPlanner.build_next_trip(
                trip=current_trip,
                candidate=candidate,
                departure_soc=departure_soc,
            )

            VeryLongTripFallbackPlanner.populate_candidate(
                trip=current_trip,
                next_trip=next_trip,
                candidate=candidate,
                departure_soc=departure_soc,
            )

            if candidate.arrival_soc < VeryLongTripFallbackPlanner.PREFERRED_MIN_ARRIVAL_SOC:
                warning = (
                    f"Low SOC charging stop selected at {candidate.charger.name}: "
                    f"estimated arrival SOC {candidate.arrival_soc:.1f}%. "
                    "No safer charger was found in the reachable route window."
                )

                existing_warnings = getattr(
                    current_trip,
                    "warnings",
                    [],
                ) or []

                if warning not in existing_warnings:
                    existing_warnings.append(
                        warning
                    )

                current_trip.warnings = existing_warnings

                candidate.warning = warning

                PlannerLogger.log(
                    warning
                )

            itinerary.add_leg(
                TripLeg(
                    number=depth + 1,
                    route=current_trip.route,
                    battery_states=getattr(current_trip, "battery_states", []),
                    results=[],
                    selected_result=candidate,
                )
            )

            visited.add(
                VeryLongTripFallbackPlanner.charger_id(
                    candidate.charger
                )
            )

            parent = TripNode(
                trip=next_trip,
                itinerary=itinerary,
                depth=depth + 1,
                parent=parent,
                visited_chargers=visited,
                g_cost=0.0,
                h_cost=0.0,
            )

            current_trip = next_trip

            PlannerLogger.log()
            PlannerLogger.log("Fallback stop selected:")
            PlannerLogger.log(f"Stop: {depth + 1}")
            PlannerLogger.log(f"Charger: {candidate.charger.name}")
            PlannerLogger.log(f"Arrival SOC: {candidate.arrival_soc:.1f}%")
            PlannerLogger.log(f"Remaining km: {current_trip.route.distance_km:.1f}")

        if completed_node is None and VeryLongTripFallbackPlanner.is_complete(current_trip):
            completed_node = TripNode(
                trip=current_trip,
                itinerary=itinerary,
                depth=len(itinerary.legs),
                parent=parent,
                visited_chargers=visited,
                g_cost=0.0,
                h_cost=0.0,
            )

        if completed_node is None:
            PlannerLogger.log("Very long trip fallback did not complete.")
            return None

        PlannerLogger.log("Very long trip fallback completed.")
        PlannerLogger.log(f"Stops: {len(itinerary.legs)}")

        return TripPlanningResult(
            recommended=completed_node,
            completed=[completed_node],
        )

    @staticmethod
    def minimum_candidate_arrival_soc(trip):
        remaining_km = VeryLongTripFallbackPlanner.route_distance_km(
            trip
        )

        if remaining_km <= 500:
            return VeryLongTripFallbackPlanner.LOW_SOC_RESCUE_MIN_ARRIVAL_SOC

        return VeryLongTripFallbackPlanner.MIN_ARRIVAL_SOC

    @staticmethod
    def preferred_candidate_arrival_soc(trip):
        return VeryLongTripFallbackPlanner.PREFERRED_MIN_ARRIVAL_SOC

    @staticmethod
    async def best_candidate(current_trip, visited):
        chargers = await VeryLongTripFallbackPlanner.find_chargers(
            current_trip
        )

        if not chargers:
            return None

        candidates = []

        for charger in chargers:
            charger_id = VeryLongTripFallbackPlanner.charger_id(charger)

            if charger_id in visited:
                continue

            route_distance = VeryLongTripFallbackPlanner.distance_from_route_start(
                current_trip,
                charger,
            )

            if route_distance < 70:
                continue

            detour_km = VeryLongTripFallbackPlanner.detour_distance_km(
                current_trip,
                charger,
            )

            arrival_soc = VeryLongTripFallbackPlanner.arrival_soc_at_distance(
                trip=current_trip,
                distance_km=route_distance,
            )

            minimum_arrival_soc = VeryLongTripFallbackPlanner.minimum_candidate_arrival_soc(
                current_trip
            )

            if arrival_soc < minimum_arrival_soc:
                continue

            try:
                setattr(charger, "route_distance_km", round(route_distance, 1))
                setattr(charger, "detour_distance_km", round(detour_km, 2))
            except Exception:
                pass

            candidate = SimpleNamespace(
                charger=charger,
                arrival_soc=round(arrival_soc, 1),
                departure_soc=None,
                soc_added=None,
                charge_added_kwh=None,
                charging_time_minutes=None,
                destination_arrival_soc=None,
                destination_soc_if_no_more_charging=None,
                requires_additional_stop=True,
                destination_reachable_from_charger=False,
                total_trip_time_minutes=None,
                score=0.0,
            )

            candidates.append(candidate)

        if not candidates:
            return None

        preferred_min_soc = VeryLongTripFallbackPlanner.preferred_candidate_arrival_soc(
            current_trip
        )

        safe_candidates = [
            candidate
            for candidate in candidates
            if candidate.arrival_soc >= preferred_min_soc
        ]

        if safe_candidates:
            sortable_candidates = safe_candidates
        else:
            sortable_candidates = candidates

        sortable_candidates.sort(
            key=lambda candidate: (
                abs(
                    candidate.arrival_soc
                    - VeryLongTripFallbackPlanner.TARGET_CHARGER_ARRIVAL_SOC
                ),
                getattr(candidate.charger, "detour_distance_km", 9999.0) or 9999.0,
                -(getattr(candidate.charger, "power_kw", 0.0) or 0.0),
            )
        )

        candidates = sortable_candidates

        return candidates[0]

    @staticmethod
    async def find_chargers(trip):
        chargers = await CorridorService.find_chargers(
            trip
        )

        if chargers:
            return chargers

        route = getattr(trip, "route", None)
        geometry = getattr(route, "geometry", []) or []

        if not geometry:
            return []

        start_km, end_km = VeryLongTripFallbackPlanner.search_window_km(
            trip
        )

        points = VeryLongTripFallbackPlanner.sample_route_window(
            geometry=geometry,
            start_km=start_km,
            end_km=end_km,
            spacing_km=20,
        )

        points = points[:16]

        if not points:
            return []

        try:
            chargers = await CorridorService.search_points(
                points,
                radius_km=110,
            )
        except TypeError:
            chargers = await CorridorService.search_points(
                points
            )

        return CorridorService.filter_chargers(
            chargers,
            trip,
        )

    @staticmethod
    def build_next_trip(trip, candidate, departure_soc):
        route_distance_to_charger = getattr(
            candidate.charger,
            "route_distance_km",
            0.0,
        ) or 0.0

        remaining_distance = max(
            0.0,
            VeryLongTripFallbackPlanner.route_distance_km(trip)
            - float(route_distance_to_charger),
        )

        average_speed = VeryLongTripFallbackPlanner.average_speed(trip)

        route = SimpleNamespace(
            distance_km=round(remaining_distance, 1),
            duration_minutes=round(
                (remaining_distance / max(35.0, average_speed)) * 60.0,
                1,
            ),
            geometry=VeryLongTripFallbackPlanner.remaining_geometry(
                trip,
                candidate.charger,
            ),
            encoded_geometry="",
            raw={
                "source": "very_long_trip_fallback",
            },
        )

        next_trip = copy.copy(trip)
        next_trip.route = route
        next_trip.battery_states = []
        next_trip.starting_soc = departure_soc

        efficiency = VeryLongTripFallbackPlanner.efficiency(trip)
        usable_battery = VeryLongTripFallbackPlanner.usable_battery_kwh(trip)
        energy_needed = remaining_distance * efficiency

        arrival_soc = max(
            0.0,
            min(
                100.0,
                departure_soc - ((energy_needed / usable_battery) * 100.0),
            ),
        )

        simulation = copy.copy(getattr(trip, "simulation", SimpleNamespace()))
        simulation.predicted_efficiency = efficiency
        simulation.energy_needed_kwh = round(energy_needed, 1)
        simulation.arrival_soc = round(arrival_soc, 1)
        simulation.average_speed = average_speed
        simulation.highway_ratio = getattr(
            simulation,
            "highway_ratio",
            0.8,
        )

        next_trip.simulation = simulation

        return next_trip

    @staticmethod
    def departure_soc_for_candidate(trip, candidate):
        arrival_soc = float(
            getattr(
                candidate,
                "arrival_soc",
                0.0,
            )
        )

        route_distance_to_charger = getattr(
            candidate.charger,
            "route_distance_km",
            0.0,
        ) or 0.0

        remaining_after_charger_km = max(
            0.0,
            VeryLongTripFallbackPlanner.route_distance_km(trip)
            - float(route_distance_to_charger),
        )

        efficiency = VeryLongTripFallbackPlanner.efficiency(
            trip
        )

        usable_battery = VeryLongTripFallbackPlanner.usable_battery_kwh(
            trip
        )

        soc_needed_after_charger = (
            remaining_after_charger_km
            * efficiency
            / usable_battery
            * 100.0
        )

        target_destination_soc = VeryLongTripFallbackPlanner.target_destination_soc(
            trip
        )

        required_departure_soc = (
            target_destination_soc
            + soc_needed_after_charger
        )

        minimum_departure_soc = arrival_soc + 8.0

        # Low-SOC rescue stop:
        # If the planner has to arrive below the preferred safety target,
        # force enough charging buffer so the next leg is not razor-thin.
        if arrival_soc < VeryLongTripFallbackPlanner.PREFERRED_MIN_ARRIVAL_SOC:
            minimum_departure_soc = max(
                minimum_departure_soc,
                arrival_soc + 30.0,
                35.0,
            )

        # Destination reachable from this charger:
        # Charge only enough to arrive with target destination SOC,
        # while still respecting low-SOC buffer rules.
        if required_departure_soc <= 100.0:
            return round(
                min(
                    100.0,
                    max(
                        minimum_departure_soc,
                        required_departure_soc,
                    ),
                ),
                1,
            )

        # Sparse final zone:
        # Charge to 100% only when needed because the next stretch has limited
        # charger coverage.
        if remaining_after_charger_km <= VeryLongTripFallbackPlanner.SPARSE_FINAL_ZONE_KM:
            return 100.0

        # Normal intermediate stop:
        # 98% avoids most of the slow 98-100% top-off but prevents extra stops
        # on sparse 2000+ km routes.
        return round(
            min(
                100.0,
                max(
                    minimum_departure_soc,
                    VeryLongTripFallbackPlanner.INTERMEDIATE_TARGET_SOC,
                ),
            ),
            1,
        )


    @staticmethod
    def populate_candidate(trip, next_trip, candidate, departure_soc):
        arrival_soc = float(candidate.arrival_soc)
        usable_battery = VeryLongTripFallbackPlanner.usable_battery_kwh(trip)

        soc_added = max(
            0.0,
            departure_soc - arrival_soc,
        )

        energy_added = usable_battery * (soc_added / 100.0)

        try:
            energy_added, charging_minutes = ChargingTimeService.estimate(
                vehicle=trip.vehicle,
                charger=candidate.charger,
                arrival_soc=arrival_soc,
                target_soc=departure_soc,
            )
        except Exception:
            power_kw = getattr(candidate.charger, "power_kw", 100.0) or 100.0
            charging_minutes = (energy_added / max(25.0, power_kw)) * 60.0 * 1.20

        detour_km = getattr(
            candidate.charger,
            "detour_distance_km",
            0.0,
        ) or 0.0

        detour_minutes = (detour_km / 50.0) * 60.0

        destination_soc = VeryLongTripFallbackPlanner.arrival_soc(next_trip)
        target_soc = VeryLongTripFallbackPlanner.target_destination_soc(trip)

        candidate.departure_soc = round(departure_soc, 1)
        candidate.soc_added = round(soc_added, 1)
        candidate.charge_added_kwh = round(energy_added, 1)
        candidate.charging_time_minutes = round(charging_minutes, 1)
        candidate.destination_arrival_soc = round(destination_soc, 1)
        candidate.destination_soc_if_no_more_charging = round(destination_soc, 1)
        candidate.requires_additional_stop = destination_soc < target_soc
        candidate.destination_reachable_from_charger = destination_soc >= target_soc
        candidate.total_trip_time_minutes = round(
            next_trip.route.duration_minutes
            + charging_minutes
            + detour_minutes,
            1,
        )
        candidate.score = round(
            1000.0
            - abs(arrival_soc - VeryLongTripFallbackPlanner.TARGET_CHARGER_ARRIVAL_SOC) * 8.0
            - detour_km * 5.0
            + (getattr(candidate.charger, "power_kw", 0.0) or 0.0),
            2,
        )

    @staticmethod
    def is_complete(trip):
        return (
            VeryLongTripFallbackPlanner.arrival_soc(trip)
            >= VeryLongTripFallbackPlanner.target_destination_soc(trip)
        )

    @staticmethod
    def arrival_soc(trip):
        simulation = getattr(trip, "simulation", None)
        value = getattr(simulation, "arrival_soc", 0.0)

        try:
            return float(value)
        except Exception:
            return 0.0

    @staticmethod
    def target_destination_soc(trip):
        planning = getattr(trip, "planning", None)
        value = getattr(planning, "target_destination_soc", 25.0)

        try:
            return float(value)
        except Exception:
            return 25.0

    @staticmethod
    def route_distance_km(trip):
        route = getattr(trip, "route", None)
        value = getattr(route, "distance_km", 0.0)

        try:
            return float(value)
        except Exception:
            return 0.0

    @staticmethod
    def efficiency(trip):
        simulation = getattr(trip, "simulation", None)

        candidates = [
            getattr(simulation, "predicted_efficiency", None),
            getattr(trip, "learned_predicted_efficiency", None),
            getattr(trip, "base_predicted_efficiency", None),
        ]

        for value in candidates:
            try:
                value = float(value)
            except Exception:
                continue

            # Some failed long-route simulations can report an extreme
            # efficiency value after arrival SOC is already 0%.
            # For fallback routing, use a realistic highway planning band.
            if 0.18 <= value <= 0.42:
                return value

        return 0.30


    @staticmethod
    def usable_battery_kwh(trip):
        vehicle = getattr(trip, "vehicle", None)
        value = getattr(vehicle, "usable_battery_kwh", 120.0)

        try:
            return max(50.0, float(value))
        except Exception:
            return 120.0

    @staticmethod
    def average_speed(trip):
        simulation = getattr(trip, "simulation", None)
        value = getattr(simulation, "average_speed", 90.0)

        try:
            return max(35.0, float(value))
        except Exception:
            return 90.0

    @staticmethod
    def arrival_soc_at_distance(trip, distance_km):
        starting_soc = getattr(trip, "starting_soc", None)

        if starting_soc is None:
            starting_soc = 100.0

        try:
            starting_soc = float(starting_soc)
        except Exception:
            starting_soc = 100.0

        energy = float(distance_km) * VeryLongTripFallbackPlanner.efficiency(trip)
        usable = VeryLongTripFallbackPlanner.usable_battery_kwh(trip)

        return max(
            0.0,
            min(
                100.0,
                starting_soc - ((energy / usable) * 100.0),
            ),
        )

    @staticmethod
    def search_window_km(trip):
        starting_soc = getattr(trip, "starting_soc", 100.0)

        try:
            starting_soc = float(starting_soc)
        except Exception:
            starting_soc = 100.0

        usable_soc = max(25.0, starting_soc - 10.0)
        estimated_range_km = VeryLongTripFallbackPlanner.usable_battery_kwh(trip) / max(
            0.22,
            VeryLongTripFallbackPlanner.efficiency(trip),
        )

        reachable_km = estimated_range_km * (usable_soc / 100.0)

        return (
            max(70.0, reachable_km * 0.50),
            max(220.0, reachable_km * 1.12),
        )

    @staticmethod
    def sample_route_window(geometry, start_km, end_km, spacing_km):
        points = []

        if not geometry:
            return points

        total = 0.0
        previous = geometry[0]
        last_added = None

        for point in geometry[1:]:
            total += VeryLongTripFallbackPlanner.distance_km(
                previous,
                point,
            )

            if start_km <= total <= end_km:
                if last_added is None or total - last_added >= spacing_km:
                    points.append(point)
                    last_added = total

            if total > end_km:
                break

            previous = point

        return points

    @staticmethod
    def distance_from_route_start(trip, charger):
        geometry = getattr(trip.route, "geometry", []) or []

        if not geometry:
            return 0.0

        charger_point = [
            getattr(charger, "longitude", 0.0),
            getattr(charger, "latitude", 0.0),
        ]

        nearest_index = VeryLongTripFallbackPlanner.nearest_geometry_index(
            geometry,
            charger_point,
        )

        distance = 0.0

        for index in range(1, nearest_index + 1):
            distance += VeryLongTripFallbackPlanner.distance_km(
                geometry[index - 1],
                geometry[index],
            )

        return distance

    @staticmethod
    def detour_distance_km(trip, charger):
        geometry = getattr(trip.route, "geometry", []) or []

        if not geometry:
            return 0.0

        charger_point = [
            getattr(charger, "longitude", 0.0),
            getattr(charger, "latitude", 0.0),
        ]

        nearest_index = VeryLongTripFallbackPlanner.nearest_geometry_index(
            geometry,
            charger_point,
        )

        return VeryLongTripFallbackPlanner.distance_km(
            charger_point,
            geometry[nearest_index],
        )

    @staticmethod
    def remaining_geometry(trip, charger):
        geometry = getattr(trip.route, "geometry", []) or []

        charger_point = [
            getattr(charger, "longitude", 0.0),
            getattr(charger, "latitude", 0.0),
        ]

        if not geometry:
            return [charger_point]

        nearest_index = VeryLongTripFallbackPlanner.nearest_geometry_index(
            geometry,
            charger_point,
        )

        return [charger_point] + geometry[nearest_index:]

    @staticmethod
    def nearest_geometry_index(geometry, point):
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
    def distance_km(point1, point2):
        lon1, lat1 = point1
        lon2, lat2 = point2

        earth_radius = 6371.0

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2.0) ** 2
        )

        return earth_radius * 2.0 * math.atan2(
            math.sqrt(a),
            math.sqrt(1.0 - a),
        )

    @staticmethod
    def charger_id(charger):
        charger_id = getattr(charger, "id", None)

        if charger_id:
            return str(charger_id)

        return (
            round(getattr(charger, "latitude", 0.0), 5),
            round(getattr(charger, "longitude", 0.0), 5),
        )
