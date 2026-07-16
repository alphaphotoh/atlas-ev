from backend.services.simulation.trip_conditions_service import (
    TripConditionsService,
)


def test_no_conditions_has_no_impact():
    result = TripConditionsService.build(
        conditions=None,
        distance_km=100,
        usable_battery_kwh=100
    )

    assert result.applied is False
    assert result.energy_impact_kwh == 0
    assert result.efficiency_adjustment_kwh_per_100km == 0
    assert result.soc_impact_percent == 0


def test_passengers_and_cargo_add_energy_impact():
    result = TripConditionsService.build(
        conditions={
            "passengers": 4,
            "cargo_weight_kg": 50
        },
        distance_km=100,
        usable_battery_kwh=100
    )

    assert result.applied is True
    assert result.energy_impact_kwh > 0
    assert result.passenger_cargo_impact_kwh > 0
    assert any(
        "Passengers" in factor
        for factor in result.factors
    )


def test_climate_and_road_condition_add_energy_impact():
    result = TripConditionsService.build(
        conditions={
            "climate_control": "high",
            "road_condition": "snow"
        },
        distance_km=200,
        usable_battery_kwh=100
    )

    assert result.applied is True
    assert result.climate_impact_kwh > 0
    assert result.road_condition_impact_kwh > 0
    assert result.energy_impact_kwh > 0


def test_eco_driving_can_reduce_energy():
    result = TripConditionsService.build(
        conditions={
            "driving_style": "eco"
        },
        distance_km=100,
        usable_battery_kwh=100
    )

    assert result.applied is True
    assert result.driving_style_impact_kwh < 0
    assert result.energy_impact_kwh < 0


def test_roof_box_and_low_tires_add_energy():
    result = TripConditionsService.build(
        conditions={
            "roof_load": "cargo_box",
            "tire_condition": "low_pressure"
        },
        distance_km=150,
        usable_battery_kwh=100
    )

    assert result.roof_load_impact_kwh > 0
    assert result.tire_impact_kwh > 0
    assert result.energy_impact_kwh > 0


def test_battery_degradation_reduces_effective_capacity():
    result = TripConditionsService.build(
        conditions={
            "battery_degradation_percent": 10
        },
        distance_km=100,
        usable_battery_kwh=100
    )

    assert result.applied is True
    assert result.battery_degradation_percent == 10
    assert result.effective_usable_battery_kwh == 90
    assert result.usable_battery_reduction_kwh == 10


def test_unknown_blank_values_are_ignored():
    result = TripConditionsService.build(
        conditions={
            "passengers": "",
            "tire_condition": "",
            "road_condition": "dry"
        },
        distance_km=100,
        usable_battery_kwh=100
    )

    assert result.energy_impact_kwh == 0