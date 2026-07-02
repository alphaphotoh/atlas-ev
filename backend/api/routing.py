from fastapi import APIRouter

from backend.services.routing_service import RoutingService

router = APIRouter(
    prefix="/route",
    tags=["Routing"]
)


@router.post("/")
async def route(start: list[float], end: list[float]):
    return await RoutingService.get_route(start, end)