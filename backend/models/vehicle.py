from dataclasses import dataclass


@dataclass
class Vehicle:

    name: str

    battery_capacity_kwh: float

    usable_battery_kwh: float

    default_efficiency: float

    dc_max_kw: float

    ac_max_kw: float

    min_arrival_soc: float

    optimal_charge_limit: float

    # Vehicle physics
    mass_kg: float

    drag_coefficient: float

    frontal_area_m2: float

    rolling_resistance: float