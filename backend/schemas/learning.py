from pydantic import BaseModel, Field


class TripObservationUploadRequest(BaseModel):
    vehicle_id: str = Field(
        ...,
        description="Vehicle identifier, for example vf9_plus"
    )

    trip_date: str | None = Field(
        default=None,
        description="Trip date in YYYY-MM-DD format"
    )

    origin: str | None = None
    destination: str | None = None

    distance_km: float = Field(
        ...,
        gt=0
    )

    starting_soc: float = Field(
        ...,
        ge=0,
        le=100
    )

    ending_soc: float = Field(
        ...,
        ge=0,
        le=100
    )

    charged_energy_kwh: float = Field(
        default=0.0,
        ge=0,
        description="Total kWh added during charging stops, if known"
    )

    actual_energy_used_kwh: float | None = Field(
        default=None,
        gt=0,
        description="Actual energy used from vehicle/app. Preferred when available."
    )

    predicted_efficiency_kwh_per_100km: float = Field(
        ...,
        gt=0
    )

    predicted_energy_used_kwh: float | None = Field(
        default=None,
        gt=0
    )

    outside_temperature_c: float | None = None
    average_speed_kmh: float | None = None
    highway_ratio: float | None = Field(
        default=None,
        ge=0,
        le=1
    )

    climate_control: str | None = None
    tire_pressure_note: str | None = None
    payload_note: str | None = None
    notes: str | None = None


class TripObservationResponse(BaseModel):
    id: str
    vehicle_id: str
    trip_date: str | None

    origin: str | None
    destination: str | None

    distance_km: float
    starting_soc: float
    ending_soc: float
    charged_energy_kwh: float

    predicted_efficiency_kwh_per_100km: float
    predicted_energy_used_kwh: float

    actual_energy_used_kwh: float
    actual_efficiency_kwh_per_100km: float

    prediction_error_percent: float
    correction_factor: float

    outside_temperature_c: float | None
    average_speed_kmh: float | None
    highway_ratio: float | None

    climate_control: str | None
    tire_pressure_note: str | None
    payload_note: str | None
    notes: str | None

    created_at: str


class LearningProfileResponse(BaseModel):
    vehicle_id: str

    observation_count: int
    total_distance_km: float

    average_predicted_efficiency_kwh_per_100km: float
    average_actual_efficiency_kwh_per_100km: float

    correction_factor: float
    average_prediction_error_percent: float

    confidence_score: float

    last_observation_id: str | None
    updated_at: str | None


class LearningUploadResponse(BaseModel):
    observation: TripObservationResponse
    profile: LearningProfileResponse


class TripObservationListResponse(BaseModel):
    vehicle_id: str
    observations: list[TripObservationResponse]