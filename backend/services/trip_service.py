from backend.models.registry import VehicleRegistry

from backend.services.learning.learning_service import LearningService
from backend.services.planning.graph_planner import GraphPlanner
from backend.services.planning.trip_builder import TripBuilder
from backend.services.planning.trip_expander import TripExpander
from backend.services.planning.waypoint_service import WaypointService
from backend.services.planning.journey_builder import JourneyBuilder
from backend.services.planning.map_response_service import MapResponseService
from backend.services.simulation.prediction_impact_service import (
    PredictionImpactService,
)
from backend.services.simulation.uncertainty_service import (
    UncertaintyService,
)


class TripService:
    DETOUR_SPEED_KMH = 50
    MAX_ALTERNATIVE_PLANS = 5
    MIN_SAFE_ARRIVAL_SOC = 10.0

    @staticmethod
    async def build_trip(
        vehicle_id: str,
        origin: str,
        waypoints: list[str],
        destination: str,
        starting_soc: float,
        average_speed: float,
        highway_ratio: float,
        waypoint_mode: str = "required_stops"
    ):
        vehicle = VehicleRegistry.get(vehicle_id)

        waypoint_mode = TripService.normalize_waypoint_mode(
            waypoint_mode
        )

        if waypoints and waypoint_mode == "via_points":
            trip = await TripBuilder.build_trip_via_points(
                vehicle=vehicle,
                origin=origin,
                waypoints=waypoints,
                destination=destination,
                starting_soc=starting_soc,
                average_speed=average_speed,
                highway_ratio=highway_ratio
            )

            planning_result = await TripExpander.expand_with_result(
                trip
            )

            itinerary = TripExpander.itinerary_from_result(
                planning_result
            )

            return TripService.build_single_trip_response(
                origin=origin,
                waypoints=waypoints,
                destination=destination,
                trip=trip,
                itinerary=itinerary,
                planning_result=planning_result,
                waypoint_mode=waypoint_mode
            )

        trip_waypoints = WaypointService.build(
            origin=origin,
            waypoints=waypoints,
            destination=destination
        )

        if len(trip_waypoints) > 1:
            journey = await JourneyBuilder.build(
                vehicle=vehicle,
                waypoints=trip_waypoints,
                starting_soc=starting_soc,
                average_speed=average_speed,
                highway_ratio=highway_ratio
            )

            return TripService.build_journey_response(
                vehicle=vehicle,
                origin=origin,
                waypoints=waypoints,
                destination=destination,
                trip_waypoints=trip_waypoints,
                journey=journey,
                waypoint_mode=waypoint_mode
            )

        trip = await TripBuilder.build_trip(
            vehicle=vehicle,
            origin=origin,
            destination=destination,
            starting_soc=starting_soc,
            average_speed=average_speed,
            highway_ratio=highway_ratio
        )

        planning_result = await TripExpander.expand_with_result(
            trip
        )

        itinerary = TripExpander.itinerary_from_result(
            planning_result
        )

        return TripService.build_single_trip_response(
            origin=origin,
            waypoints=waypoints,
            destination=destination,
            trip=trip,
            itinerary=itinerary,
            planning_result=planning_result,
            waypoint_mode=waypoint_mode
        )

    @staticmethod
    def build_journey_response(
        vehicle,
        origin,
        waypoints,
        destination,
        trip_waypoints,
        journey,
        waypoint_mode="required_stops"
    ):
        route_legs = []
        charging_stops = []
        alternative_plans = []
        alternative_plan_groups = []

        stop_number = 1

        for index, waypoint in enumerate(trip_waypoints):
            trip = journey.trips[index]
            itinerary = journey.itineraries[index]

            planning_result = None

            if index < len(journey.planning_results):
                planning_result = journey.planning_results[index]

            leg_charging_stops = TripService.build_charging_stops(
                itinerary=itinerary,
                route_leg_number=index + 1,
                start_number=stop_number
            )

            stop_number += len(leg_charging_stops)

            charging_stops.extend(
                leg_charging_stops
            )

            leg_alternatives = TripService.build_alternative_plans(
                planning_result=planning_result,
                route_leg_number=index + 1,
                original_trip=trip
            )

            alternative_plans.extend(
                leg_alternatives
            )

            if leg_alternatives:
                alternative_plan_groups.append(
                    TripService.build_alternative_plan_group(
                        route_leg_number=index + 1,
                        origin=waypoint.origin,
                        destination=waypoint.destination,
                        plans=leg_alternatives
                    )
                )

            arrival_soc_without_charging = TripService.actual_arrival_soc(
                trip
            )

            arrival_soc_with_charging = TripService.itinerary_arrival_soc(
                itinerary=itinerary,
                fallback_soc=arrival_soc_without_charging
            )

            leg_status = TripService.build_leg_status(
                route_leg_number=index + 1,
                origin=waypoint.origin,
                destination=waypoint.destination,
                arrival_soc_without_charging=arrival_soc_without_charging,
                arrival_soc_with_charging=arrival_soc_with_charging,
                charging_stops=leg_charging_stops
            )

            route_legs.append(
                {
                    "leg": index + 1,
                    "origin": waypoint.origin,
                    "destination": waypoint.destination,
                    "distance_km": TripService.round_value(
                        trip.route.distance_km,
                        1
                    ),
                    "duration_minutes": round(
                        trip.route.duration_minutes
                    ),
                    "energy_kwh": TripService.round_value(
                        trip.simulation.energy_needed_kwh,
                        1
                    ),
                    "arrival_soc_without_charging": TripService.round_value(
                        arrival_soc_without_charging,
                        1
                    ),
                    "arrival_soc_with_charging": TripService.round_value(
                        arrival_soc_with_charging,
                        1
                    ),
                    "charging_required": leg_status["charging_required"],
                    "planning_status": leg_status["planning_status"],
                    "warnings": leg_status["warnings"],
                    "charging_stop_numbers": [
                        stop["stop"]
                        for stop in leg_charging_stops
                    ]
                }
            )

        trip_planning_status = TripService.build_trip_planning_status(
            route_legs
        )

        final_arrival_soc = 0.0

        if route_legs:
            final_arrival_soc = route_legs[-1]["arrival_soc_with_charging"]

        charging_minutes = TripService.total_charging_minutes(
            charging_stops
        )

        detour_minutes = TripService.total_detour_minutes(
            charging_stops
        )

        driving_minutes = journey.total_duration_minutes

        total_trip_minutes = (
            driving_minutes +
            charging_minutes +
            detour_minutes
        )

        return {
            "vehicle": vehicle.name,
            "origin": origin,
            "destination": destination,
            "waypoints": waypoints,
            "waypoint_mode": waypoint_mode,
            "route_legs": route_legs,
            "charging_plan": {
                "charging_required": trip_planning_status["charging_required"],
                "stops": len(charging_stops),
                "planning_status": trip_planning_status["planning_status"],
                "warnings": trip_planning_status["warnings"],
                "charging_stops": charging_stops,
                "total_charging_minutes": TripService.round_value(
                    charging_minutes,
                    1
                ),
                "total_detour_minutes": TripService.round_value(
                    detour_minutes,
                    1
                )
            },
            "alternative_plans": {
                "available": len(alternative_plans) > 1,
                "scope": "per_route_leg",
                "plans": alternative_plans
            },
            "alternative_plans_by_leg": alternative_plan_groups,
            "map": MapResponseService.build(
                origin=origin,
                waypoints=waypoints,
                destination=destination,
                trips=journey.trips,
                charging_stops=charging_stops
            ),
            "learning": TripService.build_journey_learning_response(
                journey
            ),
            "summary": {
                "distance_km": TripService.round_value(
                    journey.total_distance_km,
                    1
                ),
                "driving_minutes": round(
                    driving_minutes
                ),
                "charging_minutes": TripService.round_value(
                    charging_minutes,
                    1
                ),
                "detour_minutes": TripService.round_value(
                    detour_minutes,
                    1
                ),
                "total_trip_minutes": TripService.round_value(
                    total_trip_minutes,
                    1
                ),
                "energy_kwh": TripService.round_value(
                    journey.total_energy_kwh,
                    1
                ),
                "final_arrival_soc": TripService.round_value(
                    final_arrival_soc,
                    1
                ),
                "charging_required": trip_planning_status["charging_required"],
                "planning_status": trip_planning_status["planning_status"],
                "warnings": trip_planning_status["warnings"],
                "prediction_impact": TripService.build_journey_prediction_impact_response(
                    journey
                ),
                "soc_uncertainty": TripService.build_journey_soc_uncertainty_response(
                    journey=journey,
                    estimated_arrival_soc_percent=final_arrival_soc
                )
            }
        }

    @staticmethod
    def build_single_trip_response(
        origin,
        waypoints,
        destination,
        trip,
        itinerary,
        planning_result,
        waypoint_mode="required_stops"
    ):
        charging_stops = TripService.build_charging_stops(
            itinerary=itinerary,
            route_leg_number=1,
            start_number=1
        )

        arrival_soc_without_charging = TripService.actual_arrival_soc(
            trip
        )

        arrival_soc_with_charging = TripService.itinerary_arrival_soc(
            itinerary=itinerary,
            fallback_soc=arrival_soc_without_charging
        )

        leg_status = TripService.build_leg_status(
            route_leg_number=1,
            origin=origin,
            destination=destination,
            arrival_soc_without_charging=arrival_soc_without_charging,
            arrival_soc_with_charging=arrival_soc_with_charging,
            charging_stops=charging_stops
        )

        charging_minutes = TripService.total_charging_minutes(
            charging_stops
        )

        detour_minutes = TripService.total_detour_minutes(
            charging_stops
        )

        driving_minutes = trip.route.duration_minutes

        total_trip_minutes = (
            driving_minutes +
            charging_minutes +
            detour_minutes
        )

        alternative_plans = TripService.build_alternative_plans(
            planning_result=planning_result,
            route_leg_number=1,
            original_trip=trip
        )

        alternative_plan_groups = []

        if alternative_plans:
            alternative_plan_groups.append(
                TripService.build_alternative_plan_group(
                    route_leg_number=1,
                    origin=origin,
                    destination=destination,
                    plans=alternative_plans
                )
            )

        return {
            "vehicle": trip.vehicle.name,
            "origin": origin,
            "destination": destination,
            "waypoints": waypoints,
            "waypoint_mode": waypoint_mode,
            "weather": TripService.build_weather_response(
                trip
            ),
            "route_weather": TripService.build_route_weather_response(
                trip
            ),
            "efficiency_profile": TripService.build_efficiency_profile_response(
                trip
            ),
            "route_legs": [
                {
                    "leg": 1,
                    "origin": origin,
                    "destination": destination,
                    "distance_km": TripService.round_value(
                        trip.route.distance_km,
                        1
                    ),
                    "duration_minutes": round(
                        trip.route.duration_minutes
                    ),
                    "energy_kwh": TripService.round_value(
                        trip.simulation.energy_needed_kwh,
                        1
                    ),
                    "arrival_soc_without_charging": TripService.round_value(
                        arrival_soc_without_charging,
                        1
                    ),
                    "arrival_soc_with_charging": TripService.round_value(
                        arrival_soc_with_charging,
                        1
                    ),
                    "charging_required": leg_status["charging_required"],
                    "planning_status": leg_status["planning_status"],
                    "warnings": leg_status["warnings"],
                    "charging_stop_numbers": [
                        stop["stop"]
                        for stop in charging_stops
                    ]
                }
            ],
            "charging_plan": {
                "charging_required": leg_status["charging_required"],
                "stops": len(charging_stops),
                "planning_status": leg_status["planning_status"],
                "warnings": leg_status["warnings"],
                "charging_stops": charging_stops,
                "total_charging_minutes": TripService.round_value(
                    charging_minutes,
                    1
                ),
                "total_detour_minutes": TripService.round_value(
                    detour_minutes,
                    1
                )
            },
            "alternative_plans": {
                "available": len(alternative_plans) > 1,
                "scope": "single_route",
                "plans": alternative_plans
            },
            "alternative_plans_by_leg": alternative_plan_groups,
            "map": MapResponseService.build(
                origin=origin,
                waypoints=waypoints,
                destination=destination,
                trips=[
                    trip
                ],
                charging_stops=charging_stops
            ),
            "learning": TripService.build_learning_response(
                trip
            ),
            "summary": {
                "distance_km": TripService.round_value(
                    trip.route.distance_km,
                    1
                ),
                "driving_minutes": round(
                    driving_minutes
                ),
                "charging_minutes": TripService.round_value(
                    charging_minutes,
                    1
                ),
                "detour_minutes": TripService.round_value(
                    detour_minutes,
                    1
                ),
                "total_trip_minutes": TripService.round_value(
                    total_trip_minutes,
                    1
                ),
                "predicted_efficiency": TripService.round_value(
                    trip.simulation.predicted_efficiency,
                    1
                ),
                "energy_kwh": TripService.round_value(
                    trip.simulation.energy_needed_kwh,
                    1
                ),
                "estimated_arrival_soc_without_charging": TripService.round_value(
                    trip.simulation.arrival_soc,
                    1
                ),
                "actual_arrival_soc_without_charging": TripService.round_value(
                    arrival_soc_without_charging,
                    1
                ),
                "final_arrival_soc": TripService.round_value(
                    arrival_soc_with_charging,
                    1
                ),
                "charging_required": leg_status["charging_required"],
                "planning_status": leg_status["planning_status"],
                "warnings": leg_status["warnings"],
                "prediction_impact": TripService.build_prediction_impact_response(
                    trip
                ),
                "soc_uncertainty": TripService.build_soc_uncertainty_response(
                    trip=trip,
                    estimated_arrival_soc_percent=arrival_soc_with_charging
                )
            }
        }

    @staticmethod
    def build_leg_status(
        route_leg_number,
        origin,
        destination,
        arrival_soc_without_charging,
        arrival_soc_with_charging,
        charging_stops
    ):
        warnings = []

        charging_required = TripService.is_leg_charging_required(
            arrival_soc_without_charging=arrival_soc_without_charging,
            charging_stops=charging_stops
        )

        has_charging_stops = len(
            charging_stops
        ) > 0

        arrival_soc_with_charging_value = TripService.safe_float(
            arrival_soc_with_charging,
            0.0
        )

        if not charging_required:
            planning_status = "ok"

        elif not has_charging_stops:
            planning_status = "no_feasible_charging_plan_found"

            warnings.append(
                (
                    f"Route leg {route_leg_number} "
                    f"({origin} to {destination}) requires charging "
                    "but no feasible charging stop was found."
                )
            )

        elif arrival_soc_with_charging_value <= 0:
            planning_status = "no_feasible_charging_plan_found"

            warnings.append(
                (
                    f"Route leg {route_leg_number} "
                    f"({origin} to {destination}) has charging planned "
                    "but still arrives at or below 0% SOC."
                )
            )

        else:
            planning_status = "charging_planned"

        return {
            "charging_required": charging_required,
            "planning_status": planning_status,
            "warnings": warnings
        }

    @staticmethod
    def is_leg_charging_required(
        arrival_soc_without_charging,
        charging_stops
    ):
        if charging_stops:
            return True

        arrival_soc = TripService.safe_float(
            arrival_soc_without_charging,
            0.0
        )

        return (
            arrival_soc <=
            TripService.MIN_SAFE_ARRIVAL_SOC
        )

    @staticmethod
    def build_trip_planning_status(route_legs):
        charging_required = False
        has_infeasible_leg = False
        warnings = []

        for route_leg in route_legs:
            if route_leg.get(
                "charging_required",
                False
            ):
                charging_required = True

            if (
                route_leg.get("planning_status") ==
                "no_feasible_charging_plan_found"
            ):
                has_infeasible_leg = True

            warnings.extend(
                route_leg.get(
                    "warnings",
                    []
                )
            )

        if has_infeasible_leg:
            planning_status = "incomplete_no_feasible_charging_plan"

        elif charging_required:
            planning_status = "charging_planned"

        else:
            planning_status = "ok"

        return {
            "charging_required": charging_required,
            "planning_status": planning_status,
            "warnings": warnings
        }

    @staticmethod
    def safe_float(
        value,
        default_value=0.0
    ):
        if value is None:
            return default_value

        try:
            return float(
                value
            )

        except (TypeError, ValueError):
            return default_value

    @staticmethod
    def build_journey_learning_response(journey):
        if journey is None:
            return None

        if not journey.trips:
            return None

        return TripService.build_learning_response(
            journey.trips[0]
        )

    @staticmethod
    def build_learning_response(trip):
        if trip is None:
            return None

        vehicle_id = getattr(
            trip,
            "learning_vehicle_id",
            None
        )

        correction_factor = getattr(
            trip,
            "learning_correction_factor",
            1.0
        )

        base_predicted_efficiency = getattr(
            trip,
            "base_predicted_efficiency",
            None
        )

        learned_predicted_efficiency = getattr(
            trip,
            "learned_predicted_efficiency",
            None
        )

        if learned_predicted_efficiency is None and trip.simulation:
            learned_predicted_efficiency = trip.simulation.predicted_efficiency

        profile = None

        if vehicle_id:
            profile = LearningService.get_profile(
                vehicle_id=vehicle_id
            )

        observation_count = 0
        confidence_score = 0.0
        average_predicted_efficiency = None
        average_actual_efficiency = None
        average_prediction_error_percent = None

        if profile:
            observation_count = profile.get(
                "observation_count",
                0
            )

            confidence_score = profile.get(
                "confidence_score",
                0.0
            )

            average_predicted_efficiency = profile.get(
                "average_predicted_efficiency_kwh_per_100km"
            )

            average_actual_efficiency = profile.get(
                "average_actual_efficiency_kwh_per_100km"
            )

            average_prediction_error_percent = profile.get(
                "average_prediction_error_percent"
            )

        return {
            "applied": observation_count > 0,
            "vehicle_id": vehicle_id,
            "correction_factor": TripService.round_value(
                correction_factor,
                5
            ),
            "confidence_score": TripService.round_value(
                confidence_score,
                3
            ),
            "observation_count": observation_count,
            "base_predicted_efficiency": TripService.round_value(
                base_predicted_efficiency,
                3
            ),
            "learned_predicted_efficiency": TripService.round_value(
                learned_predicted_efficiency,
                3
            ),
            "average_predicted_efficiency_kwh_per_100km": TripService.round_value(
                average_predicted_efficiency,
                3
            ),
            "average_actual_efficiency_kwh_per_100km": TripService.round_value(
                average_actual_efficiency,
                3
            ),
            "average_prediction_error_percent": TripService.round_value(
                average_prediction_error_percent,
                3
            )
        }

    @staticmethod
    def build_alternative_plan_group(
        route_leg_number,
        origin,
        destination,
        plans
    ):
        return {
            "route_leg": route_leg_number,
            "origin": origin,
            "destination": destination,
            "available": len(plans) > 1,
            "recommended_plan_id": TripService.recommended_plan_id(
                plans
            ),
            "plans": plans
        }

    @staticmethod
    def recommended_plan_id(plans):
        for plan in plans:
            if plan.get("is_recommended"):
                return plan.get("plan_id")

        return None

    @staticmethod
    def build_alternative_plans(
        planning_result,
        route_leg_number,
        original_trip
    ):
        if planning_result is None:
            return []

        nodes = TripService.unique_completed_nodes(
            planning_result=planning_result
        )

        plans = []

        for node in nodes[:TripService.MAX_ALTERNATIVE_PLANS]:
            itinerary = node.itinerary

            charging_stops = TripService.build_charging_stops(
                itinerary=itinerary,
                route_leg_number=route_leg_number,
                start_number=1
            )

            if len(charging_stops) == 0:
                continue

            charging_minutes = TripService.total_charging_minutes(
                charging_stops
            )

            detour_minutes = TripService.total_detour_minutes(
                charging_stops
            )

            total_trip_minutes = (
                original_trip.route.duration_minutes +
                charging_minutes +
                detour_minutes
            )

            final_arrival_soc = TripService.itinerary_arrival_soc(
                itinerary=itinerary,
                fallback_soc=TripService.actual_arrival_soc(
                    original_trip
                )
            )

            is_recommended = (
                planning_result.recommended is not None and
                TripService.itinerary_signature(itinerary) ==
                TripService.itinerary_signature(
                    planning_result.recommended.itinerary
                )
            )

            label = f"Alternative {len(plans) + 1}"

            if is_recommended:
                label = "Recommended"

            plans.append(
                {
                    "plan_id": (
                        f"leg-{route_leg_number}-plan-{len(plans) + 1}"
                    ),
                    "route_leg": route_leg_number,
                    "label": label,
                    "is_recommended": is_recommended,
                    "stops": len(charging_stops),
                    "charging_stops": charging_stops,
                    "total_charging_minutes": TripService.round_value(
                        charging_minutes,
                        1
                    ),
                    "total_detour_minutes": TripService.round_value(
                        detour_minutes,
                        1
                    ),
                    "estimated_total_minutes": TripService.round_value(
                        total_trip_minutes,
                        1
                    ),
                    "final_arrival_soc": TripService.round_value(
                        final_arrival_soc,
                        1
                    ),
                    "planner_cost": TripService.round_value(
                        GraphPlanner.itinerary_cost(node),
                        2
                    )
                }
            )

        return TripService.sort_alternative_plans(
            plans
        )

    @staticmethod
    def unique_completed_nodes(planning_result):
        nodes = []

        if planning_result is None:
            return nodes

        if planning_result.recommended is not None:
            nodes.append(
                planning_result.recommended
            )

        for node in planning_result.completed:
            nodes.append(
                node
            )

        unique = []
        seen = set()

        for node in nodes:
            if node is None:
                continue

            signature = TripService.itinerary_signature(
                node.itinerary
            )

            if signature in seen:
                continue

            seen.add(
                signature
            )

            unique.append(
                node
            )

        return unique

    @staticmethod
    def sort_alternative_plans(plans):
        plans.sort(
            key=lambda plan: (
                not plan["is_recommended"],
                plan["estimated_total_minutes"],
                plan["total_charging_minutes"],
                plan["stops"],
                plan["planner_cost"]
            )
        )

        return TripService.relabel_alternative_plans(
            plans
        )

    @staticmethod
    def relabel_alternative_plans(plans):
        for index, plan in enumerate(plans):
            route_leg_number = plan["route_leg"]
            plan_number = index + 1

            plan["plan_id"] = (
                f"leg-{route_leg_number}-plan-{plan_number}"
            )

            if plan["is_recommended"]:
                plan["label"] = "Recommended"
            else:
                plan["label"] = f"Alternative {plan_number}"

        return plans

    @staticmethod
    def itinerary_signature(itinerary):
        if itinerary is None:
            return tuple()

        signature = []

        for leg in itinerary.legs:
            candidate = leg.selected_result

            if candidate is None:
                continue

            charger = candidate.charger

            signature.append(
                (
                    round(
                        getattr(charger, "latitude", 0.0),
                        5
                    ),
                    round(
                        getattr(charger, "longitude", 0.0),
                        5
                    ),
                    round(
                        candidate.arrival_soc or 0.0,
                        1
                    ),
                    round(
                        candidate.departure_soc or 0.0,
                        1
                    )
                )
            )

        return tuple(signature)

    @staticmethod
    def build_charging_stops(
        itinerary,
        route_leg_number,
        start_number
    ):
        if itinerary is None:
            return []

        stops = []

        for index, leg in enumerate(itinerary.legs):
            candidate = leg.selected_result

            if candidate is None:
                continue

            charger = candidate.charger

            detour_km = getattr(
                charger,
                "detour_distance_km",
                0.0
            ) or 0.0

            detour_minutes = TripService.calculate_detour_minutes(
                detour_km
            )

            stop_number = start_number + index

            stops.append(
                {
                    "stop": stop_number,
                    "route_leg": route_leg_number,
                    "planner_leg": leg.number,
                    "charger_name": getattr(
                        charger,
                        "name",
                        "Unknown charger"
                    ),
                    "network": getattr(
                        charger,
                        "network",
                        None
                    ),
                    "power_kw": getattr(
                        charger,
                        "power_kw",
                        None
                    ),
                    "latitude": getattr(
                        charger,
                        "latitude",
                        None
                    ),
                    "longitude": getattr(
                        charger,
                        "longitude",
                        None
                    ),
                    "route_distance_km": TripService.round_value(
                        getattr(
                            charger,
                            "route_distance_km",
                            0.0
                        ),
                        1
                    ),
                    "detour_km": TripService.round_value(
                        detour_km,
                        2
                    ),
                    "detour_minutes": TripService.round_value(
                        detour_minutes,
                        1
                    ),
                    "arrival_soc": TripService.round_value(
                        candidate.arrival_soc,
                        1
                    ),
                    "departure_soc": TripService.round_value(
                        candidate.departure_soc,
                        1
                    ),
                    "soc_added": TripService.round_value(
                        candidate.departure_soc -
                        candidate.arrival_soc,
                        1
                    ),
                    "charge_added_kwh": TripService.round_value(
                        candidate.charge_added_kwh,
                        1
                    ),
                    "charging_minutes": TripService.round_value(
                        candidate.charging_time_minutes,
                        1
                    ),
                    "destination_soc_if_no_more_charging": TripService.round_value(
                        candidate.destination_arrival_soc,
                        1
                    ),
                    "total_minutes_from_this_stop": TripService.round_value(
                        candidate.total_trip_time_minutes,
                        1
                    ),
                    "score": TripService.round_value(
                        candidate.score,
                        2
                    ),
                    "is_final_stop": (
                        index ==
                        len(itinerary.legs) - 1
                    )
                }
            )

        return stops



    @staticmethod
    def build_soc_uncertainty_response(
        trip,
        estimated_arrival_soc_percent
    ):
        if trip is None:
            return None

        route = getattr(
            trip,
            "route",
            None
        )

        simulation = getattr(
            trip,
            "simulation",
            None
        )

        vehicle = getattr(
            trip,
            "vehicle",
            None
        )

        if route is None or simulation is None or vehicle is None:
            return None

        learning = TripService.build_learning_response(
            trip
        )

        learning_confidence_score = 0.0

        if learning:
            learning_confidence_score = learning.get(
                "confidence_score",
                0.0
            ) or 0.0

        uncertainty = UncertaintyService.build(
            estimated_arrival_soc_percent=estimated_arrival_soc_percent,
            usable_battery_kwh=getattr(
                vehicle,
                "usable_battery_kwh",
                None
            ),
            energy_used_kwh=getattr(
                simulation,
                "energy_needed_kwh",
                None
            ),
            distance_km=getattr(
                route,
                "distance_km",
                None
            ),
            environment_samples=getattr(
                trip,
                "environment_samples",
                []
            ) or [],
            learning_confidence_score=learning_confidence_score
        )

        return TripService.soc_uncertainty_to_response(
            uncertainty
        )

    @staticmethod
    def build_journey_soc_uncertainty_response(
        journey,
        estimated_arrival_soc_percent
    ):
        if journey is None:
            return None

        trips = getattr(
            journey,
            "trips",
            []
        ) or []

        if not trips:
            return None

        first_trip = trips[0]

        vehicle = getattr(
            first_trip,
            "vehicle",
            None
        )

        if vehicle is None:
            return None

        energy_used_kwh = 0.0
        distance_km = 0.0
        environment_samples = []

        for trip in trips:
            simulation = getattr(
                trip,
                "simulation",
                None
            )

            route = getattr(
                trip,
                "route",
                None
            )

            if simulation:
                energy_used_kwh += getattr(
                    simulation,
                    "energy_needed_kwh",
                    0.0
                ) or 0.0

            if route:
                distance_km += getattr(
                    route,
                    "distance_km",
                    0.0
                ) or 0.0

            environment_samples.extend(
                getattr(
                    trip,
                    "environment_samples",
                    []
                ) or []
            )

        learning = TripService.build_journey_learning_response(
            journey
        )

        learning_confidence_score = 0.0

        if learning:
            learning_confidence_score = learning.get(
                "confidence_score",
                0.0
            ) or 0.0

        uncertainty = UncertaintyService.build(
            estimated_arrival_soc_percent=estimated_arrival_soc_percent,
            usable_battery_kwh=getattr(
                vehicle,
                "usable_battery_kwh",
                None
            ),
            energy_used_kwh=energy_used_kwh,
            distance_km=distance_km,
            environment_samples=environment_samples,
            learning_confidence_score=learning_confidence_score
        )

        return TripService.soc_uncertainty_to_response(
            uncertainty
        )

    @staticmethod
    def soc_uncertainty_to_response(uncertainty):
        if uncertainty is None:
            return None

        return {
            "arrival_soc_most_likely_percent": getattr(
                uncertainty,
                "arrival_soc_most_likely_percent",
                None
            ),
            "arrival_soc_low_percent": getattr(
                uncertainty,
                "arrival_soc_low_percent",
                None
            ),
            "arrival_soc_high_percent": getattr(
                uncertainty,
                "arrival_soc_high_percent",
                None
            ),
            "confidence_score": getattr(
                uncertainty,
                "confidence_score",
                None
            ),
            "energy_uncertainty_kwh": getattr(
                uncertainty,
                "energy_uncertainty_kwh",
                None
            ),
            "soc_uncertainty_percent": getattr(
                uncertainty,
                "soc_uncertainty_percent",
                None
            ),
            "uncertainty_percent": getattr(
                uncertainty,
                "uncertainty_percent",
                None
            ),
            "factors": getattr(
                uncertainty,
                "factors",
                []
            ) or [],
            "warnings": getattr(
                uncertainty,
                "warnings",
                []
            ) or []
        }

    @staticmethod
    def build_prediction_impact_response(trip):
        if trip is None:
            return None

        route = getattr(
            trip,
            "route",
            None
        )

        simulation = getattr(
            trip,
            "simulation",
            None
        )

        if route is None or simulation is None:
            return None

        vehicle = getattr(
            trip,
            "vehicle",
            None
        )

        usable_battery_kwh = getattr(
            vehicle,
            "usable_battery_kwh",
            None
        )

        impact = PredictionImpactService.build(
            route=route,
            environment_samples=getattr(
                trip,
                "environment_samples",
                []
            ) or [],
            vehicle_base_efficiency=getattr(
                trip,
                "base_predicted_efficiency",
                None
            ),
            learned_efficiency=getattr(
                trip,
                "learned_predicted_efficiency",
                getattr(
                    simulation,
                    "predicted_efficiency",
                    None
                )
            ),
            final_energy_kwh=getattr(
                simulation,
                "energy_needed_kwh",
                None
            ),
            usable_battery_kwh=usable_battery_kwh
        )

        return TripService.prediction_impact_to_response(
            impact
        )

    @staticmethod
    def build_journey_prediction_impact_response(journey):
        if journey is None:
            return None

        impacts = []

        for trip in getattr(
            journey,
            "trips",
            []
        ) or []:
            impact = TripService.build_prediction_impact_response(
                trip
            )

            if impact:
                impacts.append(
                    impact
                )

        if not impacts:
            return None

        return TripService.combine_prediction_impacts(
            impacts
        )

    @staticmethod
    def prediction_impact_to_response(impact):
        if impact is None:
            return None

        fields = TripService.prediction_impact_numeric_fields()

        response = {}

        for field in fields:
            response[field] = getattr(
                impact,
                field,
                None
            )

        response["warnings"] = getattr(
            impact,
            "warnings",
            []
        ) or []

        return response

    @staticmethod
    def combine_prediction_impacts(impacts):
        response = {}

        for field in TripService.prediction_impact_numeric_fields():
            response[field] = TripService.sum_prediction_impact_field(
                impacts=impacts,
                field=field
            )

        warnings = []

        for impact in impacts:
            for warning in impact.get(
                "warnings",
                []
            ):
                if warning not in warnings:
                    warnings.append(
                        warning
                    )

        response["warnings"] = warnings

        return response

    @staticmethod
    def sum_prediction_impact_field(
        impacts,
        field
    ):
        values = []

        for impact in impacts:
            value = impact.get(
                field
            )

            if value is None:
                continue

            values.append(
                value
            )

        if not values:
            return None

        return TripService.round_value(
            sum(
                values
            ),
            2
        )

    @staticmethod
    def prediction_impact_numeric_fields():
        return [
            "vehicle_base_energy_kwh",
            "learned_base_energy_kwh",
            "final_energy_kwh",
            "learning_impact_kwh",
            "temperature_impact_kwh",
            "wind_impact_kwh",
            "elevation_impact_kwh",
            "conditions_impact_kwh",
            "total_impact_kwh",
            "learning_soc_impact_percent",
            "temperature_soc_impact_percent",
            "wind_soc_impact_percent",
            "elevation_soc_impact_percent",
            "conditions_soc_impact_percent",
            "total_soc_impact_percent",
            "elevation_gain_m",
            "elevation_loss_m",
            "net_elevation_change_m"
        ]

    @staticmethod
    def build_weather_response(trip):
        if not trip.environment_samples:
            return None

        weather = trip.environment_samples[0].weather

        return {
            "temperature_c": weather.temperature_c,
            "wind_speed_kph": weather.wind_speed_kph,
            "wind_direction_degrees": weather.wind_direction_degrees,
            "humidity_percent": weather.humidity_percent,
            "pressure_hpa": weather.pressure_hpa,
            "precipitation_mm": weather.precipitation_mm,
            "snowfall_cm": weather.snowfall_cm
        }

    @staticmethod
    def build_route_weather_response(trip):
        return [
            {
                "distance_km": TripService.round_value(
                    sample.route_distance_km,
                    1
                ),
                "temperature_c": sample.weather.temperature_c,
                "wind_speed_kph": sample.weather.wind_speed_kph,
                "wind_direction_degrees": sample.weather.wind_direction_degrees,
                "precipitation_mm": sample.weather.precipitation_mm,
                "snowfall_cm": sample.weather.snowfall_cm,
                "elevation_m": sample.elevation_m,
                "grade_percent": TripService.round_value(
                    sample.grade_percent,
                    2
                )
            }
            for sample in trip.environment_samples
        ]

    @staticmethod
    def build_efficiency_profile_response(trip):
        if not trip.efficiency_profile:
            return []

        return [
            {
                "distance_km": TripService.round_value(
                    sample.distance_km,
                    1
                ),
                "efficiency": TripService.round_value(
                    sample.efficiency,
                    2
                )
            }
            for sample in trip.efficiency_profile
        ]

    @staticmethod
    def actual_arrival_soc(trip):
        if trip.battery_states:
            return trip.battery_states[-1].soc

        if trip.simulation:
            return trip.simulation.arrival_soc

        return 0.0

    @staticmethod
    def itinerary_arrival_soc(
        itinerary,
        fallback_soc
    ):
        if itinerary is None:
            return fallback_soc

        if not itinerary.legs:
            return fallback_soc

        last_leg = itinerary.legs[-1]

        if last_leg.selected_result is None:
            return fallback_soc

        return last_leg.selected_result.destination_arrival_soc

    @staticmethod
    def total_charging_minutes(charging_stops):
        return sum(
            stop["charging_minutes"] or 0.0
            for stop in charging_stops
        )

    @staticmethod
    def total_detour_minutes(charging_stops):
        return sum(
            stop["detour_minutes"] or 0.0
            for stop in charging_stops
        )

    @staticmethod
    def calculate_detour_minutes(detour_km):
        if not detour_km:
            return 0.0

        return (
            detour_km /
            TripService.DETOUR_SPEED_KMH
        ) * 60

    @staticmethod
    def normalize_waypoint_mode(waypoint_mode):
        if waypoint_mode == "via_points":
            return "via_points"

        return "required_stops"

    @staticmethod
    def round_value(value, digits=1):
        if value is None:
            return None

        return round(
            value,
            digits
        )