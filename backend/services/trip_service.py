from backend.models.registry import VehicleRegistry
from backend.models.trip_plan import TripPlan
from backend.models.simulation_context import SimulationContext

from backend.services.adapters.geocoding_service import GeocodingService
from backend.services.adapters.routing_service import RoutingService
from backend.services.adapters.weather_service import WeatherService

from backend.services.simulation.energy_service import EnergyService
from backend.services.simulation.battery_service import BatteryService
from backend.services.simulation.battery_simulator import BatterySimulator
from backend.services.simulation.efficiency_profile_service import (
    EfficiencyProfileService,
)

from backend.services.planning.trip_expander import TripExpander
from backend.services.planning.route_weather_service import (
    RouteWeatherService,
)


class TripService:

    @staticmethod
    async def build_trip(
        vehicle_id: str,
        origin: str,
        destination: str,
        starting_soc: float,
        average_speed: float,
        highway_ratio: float
    ):

        vehicle = VehicleRegistry.get(vehicle_id)

        origin_data = await GeocodingService.search(origin)
        destination_data = await GeocodingService.search(destination)

        origin_coords = (
            origin_data["features"][0]["geometry"]["coordinates"]
        )

        destination_coords = (
            destination_data["features"][0]["geometry"]["coordinates"]
        )

        weather = await WeatherService.get_weather(

            latitude=origin_coords[1],

            longitude=origin_coords[0]

        )

        route = await RoutingService.get_route(

            origin_coords,

            destination_coords

        )

        trip = TripPlan(

            vehicle=vehicle,

            route=route

        )

        trip.weather_samples = (

            await RouteWeatherService.sample(

                route

            )

        )

        predicted_efficiency = EnergyService.predict_efficiency(

            temperature=weather.temperature_c,

            average_speed=average_speed,

            highway_ratio=highway_ratio

        )

        trip.efficiency_profile = (

            EfficiencyProfileService.build(

                route=route,

                weather_samples=trip.weather_samples,

                base_efficiency=predicted_efficiency

            )

        )

        trip.battery_states = BatterySimulator.simulate(

            route=trip.route,

            starting_soc=starting_soc,

            usable_battery_kwh=vehicle.usable_battery_kwh,

            efficiency=predicted_efficiency,

            efficiency_profile=trip.efficiency_profile

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

        trip.simulation = SimulationContext(

            predicted_efficiency=predicted_efficiency,

            energy_needed_kwh=energy_needed,

            arrival_soc=arrival_soc,

            average_speed=average_speed,

            temperature=weather.temperature_c,

            highway_ratio=highway_ratio

        )

        itinerary = await TripExpander.expand(
            trip
        )

        return {

            "vehicle": trip.vehicle.name,

            "origin": origin,

            "destination": destination,

            "weather": {

                "temperature_c": weather.temperature_c,

                "wind_speed_kph": weather.wind_speed_kph,

                "wind_direction_degrees": weather.wind_direction_degrees,

                "humidity_percent": weather.humidity_percent,

                "pressure_hpa": weather.pressure_hpa,

                "precipitation_mm": weather.precipitation_mm,

                "snowfall_cm": weather.snowfall_cm

            },

            "route_weather": [

                {

                    "distance_km": sample.route_distance_km,

                    "temperature_c": sample.weather.temperature_c,

                    "wind_speed_kph": sample.weather.wind_speed_kph,

                    "wind_direction_degrees": sample.weather.wind_direction_degrees,

                    "precipitation_mm": sample.weather.precipitation_mm,

                    "snowfall_cm": sample.weather.snowfall_cm

                }

                for sample in trip.weather_samples

            ],

            "efficiency_profile": [

                {

                    "distance_km": sample.distance_km,

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