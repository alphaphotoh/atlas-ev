from backend.services.simulation.elevation_impact_service import (
    ElevationImpactService,
)


def test_flat_route_has_no_elevation_impact():
    samples = [
        {
            "route_distance_km": 0,
            "elevation_m": 100
        },
        {
            "route_distance_km": 50,
            "elevation_m": 100
        },
        {
            "route_distance_km": 100,
            "elevation_m": 100
        }
    ]

    result = ElevationImpactService.analyze_samples(
        samples=samples,
        distance_km=100,
        usable_battery_kwh=100
    )

    assert result.elevation_gain_m == 0
    assert result.elevation_loss_m == 0
    assert result.net_energy_kwh == 0
    assert result.soc_impact_percent == 0


def test_uphill_route_has_positive_energy_impact():
    samples = [
        {
            "route_distance_km": 0,
            "elevation_m": 100
        },
        {
            "route_distance_km": 50,
            "elevation_m": 300
        },
        {
            "route_distance_km": 100,
            "elevation_m": 600
        }
    ]

    result = ElevationImpactService.analyze_samples(
        samples=samples,
        distance_km=100,
        usable_battery_kwh=100,
        vehicle_mass_kg=2900
    )

    assert result.elevation_gain_m == 500
    assert result.elevation_loss_m == 0
    assert result.net_elevation_change_m == 500
    assert result.climb_energy_kwh > 0
    assert result.net_energy_kwh > 0
    assert result.soc_impact_percent > 0


def test_downhill_recovers_some_energy():
    samples = [
        {
            "route_distance_km": 0,
            "elevation_m": 600
        },
        {
            "route_distance_km": 50,
            "elevation_m": 300
        },
        {
            "route_distance_km": 100,
            "elevation_m": 100
        }
    ]

    result = ElevationImpactService.analyze_samples(
        samples=samples,
        distance_km=100,
        usable_battery_kwh=100,
        vehicle_mass_kg=2900
    )

    assert result.elevation_gain_m == 0
    assert result.elevation_loss_m == 500
    assert result.net_elevation_change_m == -500
    assert result.regen_recovered_kwh > 0
    assert result.net_energy_kwh < 0
    assert result.soc_impact_percent < 0


def test_mixed_route_calculates_gain_and_loss():
    samples = [
        {
            "route_distance_km": 0,
            "elevation_m": 100
        },
        {
            "route_distance_km": 20,
            "elevation_m": 400
        },
        {
            "route_distance_km": 60,
            "elevation_m": 250
        },
        {
            "route_distance_km": 100,
            "elevation_m": 500
        }
    ]

    result = ElevationImpactService.analyze_samples(
        samples=samples,
        distance_km=100,
        usable_battery_kwh=100,
        vehicle_mass_kg=2900
    )

    assert result.elevation_gain_m == 550
    assert result.elevation_loss_m == 150
    assert result.net_elevation_change_m == 400
    assert result.climb_energy_kwh > result.regen_recovered_kwh
    assert result.net_energy_kwh > 0


def test_missing_elevation_samples_returns_safe_result():
    result = ElevationImpactService.analyze_samples(
        samples=[],
        distance_km=100,
        usable_battery_kwh=100
    )

    assert result.elevation_gain_m == 0
    assert result.elevation_loss_m == 0
    assert result.net_energy_kwh == 0
    assert len(result.warnings) == 1