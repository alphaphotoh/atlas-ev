from fastapi import APIRouter

from backend.api.geocoding import router as geocoding_router
from backend.api.routing import router as routing_router
from backend.api.trips import router as trip_router
from backend.api.chargers import router as charger_router

router = APIRouter()

router.include_router(geocoding_router)
router.include_router(routing_router)
router.include_router(trip_router)
router.include_router(charger_router)


@router.get("/")
def home():
    return {
        "message": "Welcome to Atlas EV API"
    }