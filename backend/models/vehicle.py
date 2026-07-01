from dataclasses import dataclass, asdict


@dataclass
class Vehicle:

    # Basic Info
    make: str
    model: str
    trim: str
    year: int

    # Battery
    battery_capacity: float
    usable_capacity: float

    # Charging
    max_dc_charge_kw: float
    max_ac_charge_kw: float

    # Dimensions
    wheel_size: int
    drag_coefficient: float
    frontal_area: float
    curb_weight: float

    # Efficiency
    default_city_efficiency: float
    default_highway_efficiency: float

    def to_dict(self):
        return asdict(self)