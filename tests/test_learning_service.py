from pathlib import Path

import pytest

from backend.schemas.learning import TripObservationUploadRequest
from backend.services.learning.learning_repository import LearningRepository
from backend.services.learning.learning_service import LearningService


@pytest.fixture
def isolated_learning_repository(tmp_path, monkeypatch):
    data_dir = tmp_path / "learning"

    monkeypatch.setattr(
        LearningRepository,
        "DATA_DIR",
        data_dir
    )

    monkeypatch.setattr(
        LearningRepository,
        "OBSERVATIONS_FILE",
        data_dir / "trip_observations.json"
    )

    monkeypatch.setattr(
        LearningRepository,
        "PROFILES_FILE",
        data_dir / "learning_profiles.json"
    )

    return data_dir


def sample_upload_request():
    return TripObservationUploadRequest(
        vehicle_id="vf9",
        trip_date="2026-07-10",
        origin="Pickering, ON",
        destination="Chicago, IL",
        distance_km=859.1,
        starting_soc=100,
        ending_soc=25.3,
        charged_energy_kwh=0.0,
        actual_energy_used_kwh=285.0,
        predicted_efficiency_kwh_per_100km=31.7,
        predicted_energy_used_kwh=272.3,
        outside_temperature_c=22,
        average_speed_kmh=97,
        highway_ratio=0.9,
        climate_control="AC on",
        tire_pressure_note="Normal",
        payload_note="Family trip",
        notes="Manual sample upload"
    )


def test_upload_trip_creates_observation_and_profile(
    isolated_learning_repository
):
    response = LearningService.upload_trip(
        sample_upload_request()
    )

    observation = response["observation"]
    profile = response["profile"]

    assert observation["vehicle_id"] == "vf9"
    assert observation["distance_km"] == 859.1
    assert observation["actual_energy_used_kwh"] == 285.0
    assert observation["actual_efficiency_kwh_per_100km"] == 33.174
    assert observation["correction_factor"] > 1.0

    assert profile["vehicle_id"] == "vf9"
    assert profile["observation_count"] == 1
    assert profile["total_distance_km"] == 859.1
    assert profile["correction_factor"] > 1.0
    assert profile["confidence_score"] > 0.0


def test_learning_profile_is_retrievable_after_upload(
    isolated_learning_repository
):
    upload_response = LearningService.upload_trip(
        sample_upload_request()
    )

    uploaded_profile = upload_response["profile"]

    profile = LearningService.get_profile(
        vehicle_id="vf9"
    )

    assert profile["vehicle_id"] == "vf9"
    assert profile["observation_count"] == 1
    assert profile["correction_factor"] == uploaded_profile["correction_factor"]
    assert profile["last_observation_id"] == uploaded_profile["last_observation_id"]


def test_list_observations_returns_uploaded_trip(
    isolated_learning_repository
):
    upload_response = LearningService.upload_trip(
        sample_upload_request()
    )

    uploaded_observation = upload_response["observation"]

    response = LearningService.list_observations(
        vehicle_id="vf9"
    )

    assert response["vehicle_id"] == "vf9"
    assert len(response["observations"]) == 1
    assert response["observations"][0]["id"] == uploaded_observation["id"]
    assert response["observations"][0]["vehicle_id"] == "vf9"


def test_empty_profile_is_returned_when_no_observations_exist(
    isolated_learning_repository
):
    profile = LearningService.get_profile(
        vehicle_id="vf9"
    )

    assert profile["vehicle_id"] == "vf9"
    assert profile["observation_count"] == 0
    assert profile["correction_factor"] == 1.0
    assert profile["confidence_score"] == 0.0


def test_actual_energy_can_be_calculated_from_soc_when_not_provided(
    isolated_learning_repository
):
    request = TripObservationUploadRequest(
        vehicle_id="vf9",
        trip_date="2026-07-10",
        origin="Pickering, ON",
        destination="Windsor, ON",
        distance_km=396.3,
        starting_soc=100,
        ending_soc=25,
        charged_energy_kwh=0.0,
        actual_energy_used_kwh=None,
        predicted_efficiency_kwh_per_100km=31.7,
        predicted_energy_used_kwh=125.6
    )

    response = LearningService.upload_trip(
        request
    )

    observation = response["observation"]

    assert observation["vehicle_id"] == "vf9"
    assert observation["actual_energy_used_kwh"] > 0
    assert observation["actual_efficiency_kwh_per_100km"] > 0


def test_unknown_vehicle_id_raises_value_error(
    isolated_learning_repository
):
    request = sample_upload_request()
    request.vehicle_id = "unknown_vehicle"

    with pytest.raises(ValueError):
        LearningService.upload_trip(
            request
        )