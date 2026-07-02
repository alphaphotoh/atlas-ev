from fastapi import APIRouter

from backend.services.geocoding_service import GeocodingService

router = APIRouter(
    prefix="/geocode",
    tags=["Geocoding"]
)


@router.get("/")
async def geocode(location: str):
    return await GeocodingService.search(location)