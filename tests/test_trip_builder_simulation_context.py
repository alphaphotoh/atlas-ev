from types import SimpleNamespace

from backend.services.planning.trip_builder import TripBuilder


def test_simulation_context_uses_battery_state_energy_and_soc():
    route = SimpleNamespace(
        distance_km=100
    )

    battery_states = [
        SimpleNamespace(
            energy_used_kwh=10,
            soc=90
        ),
        SimpleNamespace(
            energy_used_kwh=20,
            soc=70
        ),
        SimpleNamespace(
            energy_used_kwh=5,
            soc=65
        )
    ]

    context = TripBuilder.build_simulation_context(
        route=route,
        battery_states=battery_states,
        fallback_efficiency=99,
        average_speed=110,
        temperature=10,
        highway_ratio=0.8,
        starting_soc=100,
        usable_battery_kwh=100
    )

    assert context.energy_needed_kwh == 35
    assert context.arrival_soc == 65
    assert context.predicted_efficiency == 35


def test_simulation_context_falls_back_when_battery_states_are_empty():
    route = SimpleNamespace(
        distance_km=100
    )

    context = TripBuilder.build_simulation_context(
        route=route,
        battery_states=[],
        fallback_efficiency=30,
        average_speed=110,
        temperature=10,
        highway_ratio=0.8,
        starting_soc=100,
        usable_battery_kwh=100
    )

    assert context.energy_needed_kwh == 30
    assert context.arrival_soc == 70
    assert context.predicted_efficiency == 30


def test_effective_efficiency_falls_back_without_battery_states():
    efficiency = TripBuilder.effective_efficiency_from_battery_states(
        battery_states=[],
        route_distance_km=100,
        fallback_efficiency=31.5
    )

    assert efficiency == 31.5


def test_energy_used_from_battery_states_sums_segments():
    battery_states = [
        SimpleNamespace(
            energy_used_kwh=1.5
        ),
        SimpleNamespace(
            energy_used_kwh=2.5
        )
    ]

    assert TripBuilder.energy_used_from_battery_states(
        battery_states
    ) == 4.0


def test_arrival_soc_comes_from_last_battery_state():
    battery_states = [
        SimpleNamespace(
            soc=80
        ),
        SimpleNamespace(
            soc=42.25
        )
    ]

    assert TripBuilder.arrival_soc_from_battery_states(
        battery_states
    ) == 42.25