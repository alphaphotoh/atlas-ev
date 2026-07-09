from backend.models.registry import VehicleRegistry

from backend.services.planning.trip_builder import TripBuilder
from backend.services.planning.trip_expander import TripExpander
from backend.services.planning.waypoint_service import WaypointService
from backend.services.planning.journey_builder import JourneyBuilder


class TripService:
    DETOUR_SPEED_KMH = 50

    @staticmethod
    async def build_trip(
        vehicle_id: str,
        origin: str,
        waypoints: list[str],
        destination: str,
        starting_soc: float,
        average_speed: float,
        highway_ratio: float
    ):
        vehicle = VehicleRegistry.get(vehicle_id)

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
                journey=journey
            )

        trip = await TripBuilder.build_trip(
            vehicle=vehicle,
            origin=origin,
            destination=destination,
            starting_soc=starting_soc,
            average_speed=average_speed,
            highway_ratio=highway_ratio
        )

        itinerary = await TripExpander.expand(
            trip
        )

        return TripService.build_single_trip_response(
            origin=origin,
            waypoints=waypoints,
            destination=destination,
            trip=trip,
            itinerary=itinerary
        )

    @staticmethod
    def build_journey_response(
        vehicle,
        origin,
        waypoints,
        destination,
        trip_waypoints,
        journey
    ):
        route_legs = []
        charging_stops = []

        stop_number = 1

        for index, waypoint in enumerate(trip_waypoints):
            trip = journey.trips[index]
            itinerary = journey.itineraries[index]

            leg_charging_stops = TripService.build_charging_stops(
                itinerary=itinerary,
                route_leg_number=index + 1,
                start_number=stop_number
            )

            stop_number += len(leg_charging_stops)

            charging_stops.extend(
                leg_charging_stops
            )

            arrival_soc_without_charging = TripService.actual_arrival_soc(
                trip
            )

            arrival_soc_with_charging = TripService.itinerary_arrival_soc(
                itinerary=itinerary,
                fallback_soc=arrival_soc_without_charging
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
                    "charging_required": len(leg_charging_stops) > 0,
                    "charging_stop_numbers": [
                        stop["stop"]
                        for stop in leg_charging_stops
                    ]
                }
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
            "route_legs": route_legs,
            "charging_plan": {
                "charging_required": len(charging_stops) > 0,
                "stops": len(charging_stops),
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
                "charging_required": len(charging_stops) > 0
            }
        }

    @staticmethod
    def build_single_trip_response(
        origin,
        waypoints,
        destination,
        trip,
        itinerary
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

        return {
            "vehicle": trip.vehicle.name,
            "origin": origin,
            "destination": destination,
            "waypoints": waypoints,
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
                    "charging_required": len(charging_stops) > 0,
                    "charging_stop_numbers": [
                        stop["stop"]
                        for stop in charging_stops
                    ]
                }
            ],
            "charging_plan": {
                "charging_required": len(charging_stops) > 0,
                "stops": len(charging_stops),
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
                "charging_required": len(charging_stops) > 0
            }
        }

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
    def round_value(value, digits=1):
        if value is None:
            return None

        return round(
            value,
            digits
        )