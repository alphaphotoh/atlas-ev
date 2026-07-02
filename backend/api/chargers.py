from fastapi import APIRouter

from backend.services.charger_service import ChargerService

router = APIRouter(
    prefix="/chargers",
    tags=["Chargers"]
)


@router.get("/")
async def chargers(
    latitude: float,
    longitude: float,
    radius_km: float = 10
):

    return await ChargerService.search(
        latitude,
        longitude,
        radius_km
    )