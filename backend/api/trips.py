from fastapi import APIRouter

from backend.schemas.trip import TripRequest
from backend.services.trip_service import TripService

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
        temperature=request.temperature,
        average_speed=request.average_speed,
        highway_ratio=request.highway_ratio
    )