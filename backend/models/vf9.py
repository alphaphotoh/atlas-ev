from .vehicle import Vehicle

VF9 = Vehicle(

    make="VinFast",
    model="VF9",
    trim="Plus",
    year=2024,

    battery_capacity=123,
    usable_capacity=123,

    max_dc_charge_kw=160,
    max_ac_charge_kw=11.5,

    wheel_size=21,

    drag_coefficient=0.31,

    frontal_area=3.25,

    curb_weight=2890,

    default_city_efficiency=24,

    default_highway_efficiency=31
)