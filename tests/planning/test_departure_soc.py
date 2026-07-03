from backend.models.trip_planning_config import TripPlanningConfig
from backend.models.vehicle import Vehicle

from backend.services.planning.departure_soc_service import (
    DepartureSOCService,
)


vehicle = Vehicle(
    name="VF9",
    battery_capacity_kwh=130,
    usable_battery_kwh=120,
    default_efficiency=31,
    dc_max_kw=160,
    ac_max_kw=11.5,
    min_arrival_soc=10,
    optimal_charge_limit=100,
    mass_kg=2890,
    drag_coefficient=0.31,
    frontal_area_m2=2.9,
    rolling_resistance=0.011,
)

planning = TripPlanningConfig()


def test_departure_soc():

    soc = DepartureSOCService.calculate(
        vehicle=vehicle,
        remaining_distance_km=150,
        efficiency=30,
        planning=planning,
    )

    assert soc > 35
    assert soc <= 100