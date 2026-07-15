from types import SimpleNamespace

from backend.services.simulation.uncertainty_service import (
    UncertaintyService,
)


def weather(
    temperature_c=20,
    wind_speed_kph=0
):
    return SimpleNamespace(
        temperature_c=temperature_c,
        wind_speed_kph=wind_speed_kph
    )


def sample(
    temperature_c=20,
    wind_speed_kph=0,
    elevation_m=100,
    grade_percent=0
):
    return SimpleNamespace(
        weather=weather(
            temperature_c=temperature_c,
            wind_speed_kph=wind_speed_kph
        ),
        elevation_m=elevation_m,
        grade_percent=grade_percent
    )


def test_uncertainty_range_surrounds_most_likely_soc():
    result = UncertaintyService.build(
        estimated_arrival_soc_percent=25,
        usable_battery_kwh=100,
        energy_used_kwh=100,
        distance_km=300,
        environment_samples=[
            sample()
        ],
        learning_confidence_score=0.9
    )

    assert result.arrival_soc_low_percent < 25
    assert result.arrival_soc_high_percent > 25
    assert result.confidence_score > 0.8


def test_no_samples_widens_range_and_adds_warning():
    result = UncertaintyService.build(
        estimated_arrival_soc_percent=25,
        usable_battery_kwh=100,
        energy_used_kwh=100,
        distance_km=300,
        environment_samples=[],
        learning_confidence_score=0
    )

    assert result.soc_uncertainty_percent > 10
    assert len(result.warnings) >= 1
    assert "No route weather/elevation samples" in result.factors


def test_cold_weather_reduces_confidence():
    normal = UncertaintyService.build(
        estimated_arrival_soc_percent=25,
        usable_battery_kwh=100,
        energy_used_kwh=100,
        distance_km=300,
        environment_samples=[
            sample(
                temperature_c=20
            )
        ],
        learning_confidence_score=0.9
    )

    cold = UncertaintyService.build(
        estimated_arrival_soc_percent=25,
        usable_battery_kwh=100,
        energy_used_kwh=100,
        distance_km=300,
        environment_samples=[
            sample(
                temperature_c=-5
            )
        ],
        learning_confidence_score=0.9
    )

    assert cold.soc_uncertainty_percent > normal.soc_uncertainty_percent
    assert cold.confidence_score < normal.confidence_score


def test_high_wind_adds_factor():
    result = UncertaintyService.build(
        estimated_arrival_soc_percent=25,
        usable_battery_kwh=100,
        energy_used_kwh=100,
        distance_km=300,
        environment_samples=[
            sample(
                wind_speed_kph=35
            )
        ],
        learning_confidence_score=0.9
    )

    assert "High wind risk" in result.factors


def test_low_conservative_soc_adds_warning():
    result = UncertaintyService.build(
        estimated_arrival_soc_percent=8,
        usable_battery_kwh=100,
        energy_used_kwh=100,
        distance_km=300,
        environment_samples=[
            sample()
        ],
        learning_confidence_score=0.9
    )

    assert result.arrival_soc_low_percent < 8
    assert any(
        "10% safety buffer" in warning
        for warning in result.warnings
    )