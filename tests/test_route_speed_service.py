from types import SimpleNamespace

from backend.services.simulation.route_speed_service import RouteSpeedService


def test_route_speed_uses_route_distance_and_duration():
    route = SimpleNamespace(
        distance_km=397.4,
        duration_minutes=258,
    )

    result = RouteSpeedService.estimate(
        route=route,
        fallback_average_speed_kmh=110,
    )

    assert result.average_speed_kmh == 92.4
    assert result.source == "route_distance_and_duration"
    assert result.confidence == "high"
    assert result.fallback_used is False


def test_route_speed_uses_fallback_when_route_duration_missing():
    route = SimpleNamespace(
        distance_km=397.4,
        duration_minutes=None,
    )

    result = RouteSpeedService.estimate(
        route=route,
        fallback_average_speed_kmh=110,
    )

    assert result.average_speed_kmh == 110
    assert result.source == "fallback_average_speed"
    assert result.confidence == "low"
    assert result.fallback_used is True


def test_route_speed_clamps_unreasonable_fallback():
    route = SimpleNamespace(
        distance_km=None,
        duration_minutes=None,
    )

    result = RouteSpeedService.estimate(
        route=route,
        fallback_average_speed_kmh=999,
    )

    assert result.average_speed_kmh == 130