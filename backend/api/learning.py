from fastapi import APIRouter, HTTPException

from backend.schemas.learning import (
    LearningProfileResponse,
    LearningUploadResponse,
    TripObservationListResponse,
    TripObservationUploadRequest,
)
from backend.services.learning.learning_service import LearningService


router = APIRouter(
    prefix="/learning",
    tags=["Learning"]
)


@router.post(
    "/upload-trip",
    response_model=LearningUploadResponse
)
async def upload_trip_observation(
    request: TripObservationUploadRequest
):
    try:
        return LearningService.upload_trip(
            request
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error


@router.get(
    "/profile/{vehicle_id}",
    response_model=LearningProfileResponse
)
async def get_learning_profile(
    vehicle_id: str
):
    return LearningService.get_profile(
        vehicle_id=vehicle_id
    )


@router.get(
    "/observations/{vehicle_id}",
    response_model=TripObservationListResponse
)
async def list_trip_observations(
    vehicle_id: str
):
    return LearningService.list_observations(
        vehicle_id=vehicle_id
    )