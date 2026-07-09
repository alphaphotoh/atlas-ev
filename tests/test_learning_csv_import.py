import pytest

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


def test_import_csv_text_imports_multiple_vf9_trips(
    isolated_learning_repository
):
    csv_text = """vehicle_id,trip_date,origin,destination,distance_km,starting_soc,ending_soc,charged_energy_kwh,actual_energy_used_kwh,predicted_efficiency_kwh_per_100km,predicted_energy_used_kwh,outside_temperature_c,average_speed_kmh,highway_ratio,climate_control,tire_pressure_note,payload_note,notes
vf9,2026-07-10,"Pickering, ON","Chicago, IL",859.1,100,25.3,0,285,31.7,272.3,22,97,0.9,AC on,Normal,Family trip,Manual sample upload
vf9,2026-07-11,"Pickering, ON","Ottawa, ON",397.4,100,20,0,126,31.0,123.2,21,95,0.85,AC on,Normal,Light load,Second sample upload
"""

    response = LearningService.import_csv_text(
        csv_text
    )

    assert response["vehicle_id"] == "vf9"
    assert response["imported_count"] == 2
    assert response["failed_count"] == 0
    assert len(response["observations"]) == 2
    assert response["profile"]["vehicle_id"] == "vf9"
    assert response["profile"]["observation_count"] == 2
    assert response["profile"]["correction_factor"] > 1.0


def test_import_csv_text_collects_row_errors_without_stopping(
    isolated_learning_repository
):
    csv_text = """vehicle_id,trip_date,origin,destination,distance_km,starting_soc,ending_soc,charged_energy_kwh,actual_energy_used_kwh,predicted_efficiency_kwh_per_100km,predicted_energy_used_kwh
vf9,2026-07-10,"Pickering, ON","Chicago, IL",859.1,100,25.3,0,285,31.7,272.3
vf9,2026-07-11,"Pickering, ON","Ottawa, ON",,100,20,0,126,31.0,123.2
"""

    response = LearningService.import_csv_text(
        csv_text
    )

    assert response["vehicle_id"] == "vf9"
    assert response["imported_count"] == 1
    assert response["failed_count"] == 1
    assert len(response["observations"]) == 1
    assert len(response["errors"]) == 1
    assert response["errors"][0]["row_number"] == 3
    assert "distance_km" in response["errors"][0]["error"]


def test_import_csv_text_rejects_empty_csv(
    isolated_learning_repository
):
    with pytest.raises(ValueError):
        LearningService.import_csv_text(
            ""
        )


def test_import_csv_text_supports_column_aliases(
    isolated_learning_repository
):
    csv_text = """vehicle,date,from,to,distance,start_soc,end_soc,energy_used_kwh,predicted_efficiency,predicted_energy_kwh
vf9,2026-07-10,"Pickering, ON","Chicago, IL",859.1,100,25.3,285,31.7,272.3
"""

    response = LearningService.import_csv_text(
        csv_text
    )

    assert response["imported_count"] == 1
    assert response["failed_count"] == 0
    assert response["observations"][0]["vehicle_id"] == "vf9"
    assert response["observations"][0]["actual_energy_used_kwh"] == 285.0


def test_import_csv_text_can_calculate_actual_energy_from_soc(
    isolated_learning_repository
):
    csv_text = """vehicle_id,trip_date,origin,destination,distance_km,starting_soc,ending_soc,charged_energy_kwh,predicted_efficiency_kwh_per_100km,predicted_energy_used_kwh
vf9,2026-07-10,"Pickering, ON","Windsor, ON",396.3,100,25,0,31.7,125.6
"""

    response = LearningService.import_csv_text(
        csv_text
    )

    observation = response["observations"][0]

    assert response["imported_count"] == 1
    assert observation["actual_energy_used_kwh"] > 0
    assert observation["actual_efficiency_kwh_per_100km"] > 0