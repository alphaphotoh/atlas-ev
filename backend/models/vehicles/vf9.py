from backend.models.vehicle import Vehicle


VF9 = Vehicle(

    name="2024 VinFast VF9 Plus",

    battery_capacity_kwh=130,

    usable_battery_kwh=120,

    default_efficiency=31.0,

    dc_max_kw=160,

    ac_max_kw=11.5,

    min_arrival_soc=15,

    optimal_charge_limit=90,

    mass_kg = 2890,

    drag_coefficient = 0.31,

    frontal_area_m2 = 2.9,

    rolling_resistance = 0.011,
)