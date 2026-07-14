from types import SimpleNamespace
import asyncio

from backend.models.trip_planning_config import TripPlanningConfig
from backend.services.planning.optimizer.departure_optimizer import DepartureOptimizer
from backend.services.simulation.charge_curve import ChargeCurve
from backend.services.simulation.charging_time_service import ChargingTimeService


def fake_vehicle():
    return SimpleNamespace(
        usable_battery_kwh=108.0,
        dc_max_kw=180.0
    )


def fake_charger(**kwargs):
    values = {
        "name": "Test Charger",
        "power_kw": 180.0,
        "latitude": 45.0,
        "longitude": -75.0,
        "is_sparse_route": False,
        "reliability_score": None,
    }

    values.update(kwargs)

    return SimpleNamespace(**values)


def fake_trip(planning=None):
    return SimpleNamespace(
        planning=planning or TripPlanningConfig(),
        vehicle=fake_vehicle(),
        is_sparse_route=False,
    )


def trip_with_arrival_soc(arrival_soc):
    return SimpleNamespace(
        battery_states=[],
        simulation=SimpleNamespace(
            arrival_soc=arrival_soc
        ),
        route=SimpleNamespace(
            duration_minutes=60.0
        )
    )


def test_charge_curve_taper_is_slower_than_peak_zone():
    vehicle = fake_vehicle()
    charger = fake_charger()
    curve = ChargeCurve.default_vf9()

    fast_zone = curve.average_minutes_per_percent(
        vehicle=vehicle,
        charger=charger,
        start_soc=10.0,
        end_soc=25.0
    )

    taper_zone = curve.average_minutes_per_percent(
        vehicle=vehicle,
        charger=charger,
        start_soc=85.0,
        end_soc=100.0
    )

    assert taper_zone > fast_zone * 2.0


def test_charging_time_service_uses_curve():
    vehicle = fake_vehicle()
    charger = fake_charger()

    _, minutes_to_80 = ChargingTimeService.estimate(
        vehicle=vehicle,
        charger=charger,
        arrival_soc=20.0,
        target_soc=80.0
    )

    _, minutes_to_100 = ChargingTimeService.estimate(
        vehicle=vehicle,
        charger=charger,
        arrival_soc=20.0,
        target_soc=100.0
    )

    assert minutes_to_100 > minutes_to_80


def test_non_final_default_options_do_not_exceed_85(monkeypatch):
    async def fake_build(trip, charger, departure_soc):
        return trip_with_arrival_soc(0.0)

    monkeypatch.setattr(
        "backend.services.planning.optimizer.departure_optimizer.TripBuilder.build",
        fake_build
    )

    trip = fake_trip()
    charger = fake_charger()

    options = asyncio.run(
        DepartureOptimizer.optimize_options(
            trip=trip,
            charger=charger,
            arrival_soc=20.0
        )
    )

    departure_socs = [soc for soc, _ in options]

    assert departure_socs
    assert max(departure_socs) <= 85.0


def test_sparse_route_buffer_increases_non_final_target(monkeypatch):
    async def fake_build(trip, charger, departure_soc):
        return trip_with_arrival_soc(0.0)

    monkeypatch.setattr(
        "backend.services.planning.optimizer.departure_optimizer.TripBuilder.build",
        fake_build
    )

    trip = fake_trip()

    normal_options = asyncio.run(
        DepartureOptimizer.optimize_options(
            trip=trip,
            charger=fake_charger(),
            arrival_soc=20.0
        )
    )

    sparse_options = asyncio.run(
        DepartureOptimizer.optimize_options(
            trip=trip,
            charger=fake_charger(is_sparse_route=True),
            arrival_soc=20.0
        )
    )

    normal_max = max(soc for soc, _ in normal_options)
    sparse_max = max(soc for soc, _ in sparse_options)

    assert sparse_max > normal_max


def test_config_allows_low_intermediate_arrival_floor():
    planning = TripPlanningConfig(
        minimum_charger_arrival_soc=10.0,
        min_arrival_soc=10.0
    )

    assert planning.minimum_charger_arrival_soc == 10.0
    assert planning.min_arrival_soc == 10.0


def test_changing_min_arrival_soc_is_config_only():
    low = TripPlanningConfig(
        minimum_charger_arrival_soc=10.0
    )

    higher = TripPlanningConfig(
        minimum_charger_arrival_soc=15.0
    )

    assert low.minimum_charger_arrival_soc == 10.0
    assert higher.minimum_charger_arrival_soc == 15.0


def test_final_destination_target_is_separate_from_min_arrival(monkeypatch):
    async def fake_build(trip, charger, departure_soc):
        return trip_with_arrival_soc(
            departure_soc - 55.0
        )

    monkeypatch.setattr(
        "backend.services.planning.optimizer.departure_optimizer.TripBuilder.build",
        fake_build
    )

    planning = TripPlanningConfig(
        minimum_charger_arrival_soc=10.0,
        target_destination_soc=25.0,
        destination_target_soc=25.0
    )

    trip = fake_trip(planning=planning)
    charger = fake_charger()

    options = asyncio.run(
        DepartureOptimizer.optimize_options(
            trip=trip,
            charger=charger,
            arrival_soc=20.0
        )
    )

    departure_soc, next_trip = options[0]

    assert 79.0 <= departure_soc <= 81.0
    assert 24.0 <= DepartureOptimizer.destination_soc(next_trip) <= 26.0