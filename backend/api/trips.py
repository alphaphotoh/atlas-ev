from fastapi import APIRouter

from backend.schemas.trip import TripRequest
from backend.schemas.trip_response import TripResponse
from backend.services.adapters.weather_service import WeatherService
from backend.services.trip_service import TripService


router = APIRouter(
    prefix="/trip",
    tags=["Trip Planner"]
)


@router.post(
    "/",
    response_model=TripResponse,
    response_model_exclude_none=True
)
async def plan_trip(request: TripRequest):
    vehicle_id = getattr(
        request,
        "vehicle_id",
        None
    )

    if vehicle_id is None:
        vehicle_id = getattr(
            request,
            "vehicle",
            None
        )

    return await TripService.build_trip(
        vehicle_id=vehicle_id,
        origin=request.origin,
        waypoints=request.waypoints,
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