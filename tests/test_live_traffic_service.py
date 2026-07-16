from backend.services.adapters.live_traffic_service import (
    LiveTrafficService,
)


def test_parse_google_duration_seconds():
    assert LiveTrafficService.parse_duration_seconds("123.5s") == 123.5
    assert LiveTrafficService.parse_duration_seconds("120s") == 120
    assert LiveTrafficService.parse_duration_seconds(None) is None
    assert LiveTrafficService.parse_duration_seconds("bad") is None


def test_normalize_ors_coordinate_order():
    result = LiveTrafficService.normalize_coordinate(
        [-79.123, 43.456]
    )

    assert result["latitude"] == 43.456
    assert result["longitude"] == -79.123


def test_normalize_lat_lon_coordinate_order():
    result = LiveTrafficService.normalize_coordinate(
        [43.456, -79.123]
    )

    assert result["latitude"] == 43.456
    assert result["longitude"] == -79.123