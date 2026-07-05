from fastapi import APIRouter

from backend.schemas.trip import TripRequest
from backend.services.trip_service import TripService
from backend.services.adapters.weather_service import WeatherService

router = APIRouter(
    prefix="/trip",
    tags=["Trip Planner"]
)


@router.post("/")
async def plan_trip(request: TripRequest):

    return await TripService.build_trip(

        vehicle_id=request.vehicle,

        origin=request.origin,

        destination=request.destination,

        starting_soc=request.starting_soc,

        average_speed=request.average_speed,

        highway_ratio=request.highway_ratio

    )


@router.get("/weather")
async def weather(
    latitude: float,
    longitude: float
):

    return await WeatherService.get_weather(

        latitude=latitude,

        longitude=longitude

    )