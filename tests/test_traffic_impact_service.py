from backend.services.simulation.traffic_impact_service import (
    TrafficImpactService,
)


def test_no_traffic_mode_has_no_impact():
    result = TrafficImpactService.build(
        traffic_mode="none",
        distance_km=100,
        duration_minutes=60,
        highway_ratio=0.8,
        usable_battery_kwh=100
    )

    assert result.applied is False
    assert result.extra_duration_minutes == 0
    assert result.energy_impact_kwh == 0
    assert result.duration_multiplier == 1.0


def test_estimated_traffic_adds_time_and_energy():
    result = TrafficImpactService.build(
        traffic_mode="estimated",
        distance_km=200,
        duration_minutes=120,
        highway_ratio=0.8,
        usable_battery_kwh=100
    )

    assert result.applied is True
    assert result.extra_duration_minutes > 0
    assert result.adjusted_duration_minutes > 120
    assert result.energy_impact_kwh > 0
    assert result.soc_impact_percent > 0


def test_live_traffic_falls_back_to_estimated_until_connected():
    result = TrafficImpactService.build(
        traffic_mode="live",
        distance_km=200,
        duration_minutes=120,
        highway_ratio=0.8,
        usable_battery_kwh=100
    )

    assert result.applied is True
    assert result.mode == "live"
    assert result.extra_duration_minutes > 0
    assert any(
        "Live traffic is not connected yet" in warning
        for warning in result.warnings
    )


def test_heavy_traffic_has_more_impact_than_light_traffic():
    light = TrafficImpactService.build(
        traffic_mode="estimated",
        traffic_level="light",
        distance_km=200,
        duration_minutes=120,
        highway_ratio=0.5,
        usable_battery_kwh=100
    )

    heavy = TrafficImpactService.build(
        traffic_mode="estimated",
        traffic_level="heavy",
        distance_km=200,
        duration_minutes=120,
        highway_ratio=0.5,
        usable_battery_kwh=100
    )

    assert heavy.extra_duration_minutes > light.extra_duration_minutes
    assert heavy.energy_impact_kwh > light.energy_impact_kwh


def test_city_route_has_more_traffic_penalty_than_highway_route():
    city = TrafficImpactService.build(
        traffic_mode="estimated",
        distance_km=100,
        duration_minutes=60,
        highway_ratio=0.2,
        usable_battery_kwh=100
    )

    highway = TrafficImpactService.build(
        traffic_mode="estimated",
        distance_km=100,
        duration_minutes=60,
        highway_ratio=0.9,
        usable_battery_kwh=100
    )

    assert city.extra_duration_minutes > highway.extra_duration_minutes
    assert city.energy_impact_kwh > highway.energy_impact_kwh


def test_invalid_mode_is_treated_as_none():
    result = TrafficImpactService.build(
        traffic_mode="bad-value",
        distance_km=100,
        duration_minutes=60,
        highway_ratio=0.8,
        usable_battery_kwh=100
    )

    assert result.applied is False
    assert result.mode == "none"