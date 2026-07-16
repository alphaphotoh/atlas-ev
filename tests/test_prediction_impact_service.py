from types import SimpleNamespace

from backend.services.simulation.prediction_impact_service import (
    PredictionImpactService,
)


def weather(
    temperature_c=20,
    wind_speed_kph=0,
    wind_direction_degrees=0
):
    return SimpleNamespace(
        temperature_c=temperature_c,
        wind_speed_kph=wind_speed_kph,
        wind_direction_degrees=wind_direction_degrees
    )


def sample(
    distance_km,
    temperature_c=20,
    wind_speed_kph=0,
    wind_direction_degrees=0,
    elevation_m=None,
    grade_percent=0
):
    return SimpleNamespace(
        route_distance_km=distance_km,
        weather=weather(
            temperature_c=temperature_c,
            wind_speed_kph=wind_speed_kph,
            wind_direction_degrees=wind_direction_degrees
        ),
        elevation_m=elevation_m,
        grade_percent=grade_percent
    )


def route(distance_km=100):
    return SimpleNamespace(
        distance_km=distance_km
    )


def test_no_conditions_gives_base_energy():
    result = PredictionImpactService.build(
        route=route(100),
        environment_samples=[],
        vehicle_base_efficiency=30,
        learned_efficiency=30,
        final_energy_kwh=30,
        usable_battery_kwh=100
    )

    assert result.vehicle_base_energy_kwh == 30
    assert result.learned_base_energy_kwh == 30
    assert result.final_energy_kwh == 30
    assert result.total_impact_kwh == 0
    assert len(result.warnings) >= 1


def test_learning_impact_is_calculated():
    result = PredictionImpactService.build(
        route=route(100),
        environment_samples=[],
        vehicle_base_efficiency=30,
        learned_efficiency=33,
        final_energy_kwh=33,
        usable_battery_kwh=100
    )

    assert result.vehicle_base_energy_kwh == 30
    assert result.learned_base_energy_kwh == 33
    assert result.learning_impact_kwh == 3
    assert result.learning_soc_impact_percent == 3


def test_cold_temperature_adds_energy():
    samples = [
        sample(
            distance_km=100,
            temperature_c=0
        )
    ]

    result = PredictionImpactService.build(
        route=route(100),
        environment_samples=samples,
        vehicle_base_efficiency=30,
        learned_efficiency=30,
        final_energy_kwh=None,
        usable_battery_kwh=100
    )

    assert result.temperature_impact_kwh > 0
    assert result.final_energy_kwh > result.learned_base_energy_kwh


def test_uphill_grade_adds_elevation_energy():
    samples = [
        sample(
            distance_km=50,
            temperature_c=20,
            elevation_m=100,
            grade_percent=0
        ),
        sample(
            distance_km=100,
            temperature_c=20,
            elevation_m=300,
            grade_percent=4
        )
    ]

    result = PredictionImpactService.build(
        route=route(100),
        environment_samples=samples,
        vehicle_base_efficiency=30,
        learned_efficiency=30,
        final_energy_kwh=None,
        usable_battery_kwh=100
    )

    assert result.elevation_impact_kwh > 0
    assert result.elevation_gain_m == 200


def test_final_energy_overrides_calculated_energy():
    samples = [
        sample(
            distance_km=100,
            temperature_c=0
        )
    ]

    result = PredictionImpactService.build(
        route=route(100),
        environment_samples=samples,
        vehicle_base_efficiency=30,
        learned_efficiency=30,
        final_energy_kwh=40,
        usable_battery_kwh=100
    )

    assert result.final_energy_kwh == 40
    assert result.total_impact_kwh == 10
    assert result.total_soc_impact_percent == 10