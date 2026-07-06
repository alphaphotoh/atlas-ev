from backend.models.registry import VehicleRegistry

from backend.services.planning.trip_builder import (
    TripBuilder,
)

from backend.services.planning.trip_expander import (
    TripExpander,
)

from backend.services.planning.waypoint_service import (
    WaypointService,
)

from backend.services.planning.journey_builder import (
    JourneyBuilder,
)


class TripService:

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

        #
        # Multi-leg trip
        #
        if len(trip_waypoints) > 1:

            journey = await JourneyBuilder.build(

                vehicle=vehicle,

                waypoints=trip_waypoints,

                starting_soc=starting_soc,

                average_speed=average_speed,

                highway_ratio=highway_ratio

            )

            return {

                "vehicle": vehicle.name,

                "origin": origin,

                "destination": destination,

                "waypoints": waypoints,

                "legs": [

                    {

                        "origin": waypoint.origin,

                        "destination": waypoint.destination,

                        "distance_km": round(
                            trip.route.distance_km,
                            1
                        ),

                        "duration_minutes": round(
                            trip.route.duration_minutes
                        ),

                        "arrival_soc": round(
                            trip.simulation.arrival_soc,
                            1
                        )

                    }

                    for waypoint, trip in zip(

                        trip_waypoints,

                        journey.trips

                    )

                ],

                "summary": {

                    "distance_km": round(

                        journey.total_distance_km,

                        1

                    ),

                    "duration_minutes": round(

                        journey.total_duration_minutes

                    ),

                    "energy_kwh": round(

                        journey.total_energy_kwh,

                        1

                    ),

                    "arrival_soc": round(

                        journey.arrival_soc,

                        1

                    )

                }

            }

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

        return {

            "vehicle": trip.vehicle.name,

            "origin": origin,

            "waypoints": waypoints,

            "destination": destination,

            "weather": {

                "temperature_c": trip.environment_samples[0].weather.temperature_c,

                "wind_speed_kph": trip.environment_samples[0].weather.wind_speed_kph,

                "wind_direction_degrees": trip.environment_samples[0].weather.wind_direction_degrees,

                "humidity_percent": trip.environment_samples[0].weather.humidity_percent,

                "pressure_hpa": trip.environment_samples[0].weather.pressure_hpa,

                "precipitation_mm": trip.environment_samples[0].weather.precipitation_mm,

                "snowfall_cm": trip.environment_samples[0].weather.snowfall_cm

            },

            "route_weather": [

                {

                    "distance_km": round(
                        sample.route_distance_km,
                        1
                    ),

                    "temperature_c": sample.weather.temperature_c,

                    "wind_speed_kph": sample.weather.wind_speed_kph,

                    "wind_direction_degrees": sample.weather.wind_direction_degrees,

                    "precipitation_mm": sample.weather.precipitation_mm,

                    "snowfall_cm": sample.weather.snowfall_cm,

                    "elevation_m": sample.elevation_m,

                    "grade_percent": round(
                        sample.grade_percent,
                        2
                    )

                }

                for sample in trip.environment_samples

            ],

            "efficiency_profile": [

                {

                    "distance_km": round(
                        sample.distance_km,
                        1
                    ),

                    "efficiency": sample.efficiency

                }

                for sample in trip.efficiency_profile

            ],

            "distance_km": round(
                trip.route.distance_km,
                1
            ),

            "duration_minutes": round(
                trip.route.duration_minutes
            ),

            "predicted_efficiency": round(
                trip.simulation.predicted_efficiency,
                1
            ),

            "energy_needed_kwh": round(
                trip.simulation.energy_needed_kwh,
                1
            ),

            "estimated_arrival_soc": round(
                trip.simulation.arrival_soc,
                1
            ),

            "charging_required": (
                trip.simulation.arrival_soc
                < trip.vehicle.min_arrival_soc
            ),

            "legs": [

                {

                    "leg": leg.number,

                    "distance_km": round(
                        leg.route.distance_km,
                        1
                    ),

                    "duration_minutes": round(
                        leg.route.duration_minutes
                    ),

                    "charger": (
                        leg.selected_result
                        .candidate
                        .charger
                        .name
                    ),

                    "network": (
                        leg.selected_result
                        .candidate
                        .charger
                        .network
                    ),

                    "power_kw": (
                        leg.selected_result
                        .candidate
                        .charger
                        .power_kw
                    ),

                    "arrival_soc": round(
                        leg.selected_result
                        .candidate
                        .arrival_soc,
                        1
                    ),

                    "departure_soc": round(
                        leg.selected_result
                        .candidate
                        .departure_soc,
                        1
                    ),

                    "destination_soc": round(
                        leg.selected_result
                        .destination_soc,
                        1
                    ),

                    "charging_minutes": round(
                        leg.selected_result
                        .charging_time_minutes,
                        1
                    ),

                    "driving_minutes": round(
                        leg.selected_result
                        .driving_time_minutes,
                        1
                    ),

                    "detour_minutes": round(
                        leg.selected_result
                        .detour_time_minutes,
                        1
                    ),

                    "total_minutes": round(
                        leg.selected_result
                        .total_trip_time_minutes,
                        1
                    )

                }

                for leg in itinerary.legs

            ],

            "summary": {

                "stops": itinerary.stops,

                "total_driving_minutes": round(
                    itinerary.total_driving_minutes,
                    1
                ),

                "total_charging_minutes": round(
                    itinerary.total_charging_minutes,
                    1
                ),

                "total_detour_minutes": round(
                    itinerary.total_detour_minutes,
                    1
                ),

                "total_trip_minutes": round(
                    itinerary.total_trip_minutes,
                    1
                )

            }

        }