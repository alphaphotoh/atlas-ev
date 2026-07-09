from fastapi.testclient import TestClient

from backend.main import app
from backend.services.learning.csv_template_service import CsvTemplateService


def test_csv_template_service_builds_template():
    csv_text = CsvTemplateService.build_template()

    assert "vehicle_id" in csv_text
    assert "trip_date" in csv_text
    assert "distance_km" in csv_text
    assert "predicted_efficiency_kwh_per_100km" in csv_text
    assert "vf9" in csv_text
    assert "Pickering, ON" in csv_text


def test_learning_template_csv_endpoint_downloads_csv():
    client = TestClient(
        app
    )

    response = client.get(
        "/learning/template-csv"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/csv"
    )

    content_disposition = response.headers.get(
        "content-disposition",
        ""
    )

    assert "attachment" in content_disposition
    assert "atlas_ev_learning_template.csv" in content_disposition

    csv_text = response.text

    assert "vehicle_id" in csv_text
    assert "trip_date" in csv_text
    assert "distance_km" in csv_text
    assert "vf9" in csv_text