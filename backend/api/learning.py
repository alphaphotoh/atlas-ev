from fastapi import APIRouter, File, HTTPException, Response, UploadFile

from backend.schemas.learning import (
    LearningProfileResponse,
    LearningUploadResponse,
    TripObservationImportResponse,
    TripObservationListResponse,
    TripObservationUploadRequest,
)
from backend.services.learning.csv_template_service import CsvTemplateService
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


@router.post(
    "/import-csv",
    response_model=TripObservationImportResponse
)
async def import_trip_observations_csv(
    file: UploadFile = File(...)
):
    try:
        content = await file.read()

        csv_text = content.decode(
            "utf-8-sig"
        )

        return LearningService.import_csv_text(
            csv_text=csv_text
        )

    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail="CSV file must be UTF-8 encoded"
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error


@router.get(
    "/template-csv"
)
async def download_learning_csv_template():
    csv_text = CsvTemplateService.build_template()

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{CsvTemplateService.FILENAME}"'
            )
        }
    )


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