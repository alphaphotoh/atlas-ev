from dataclasses import dataclass


@dataclass
class TripPlanningConfig:
    minimum_charger_arrival_soc: float = 5.0

    ideal_charger_arrival_soc_min: float = 23.0
    ideal_charger_arrival_soc_max: float = 31.0

    target_destination_soc: float = 25.0
    safety_buffer_soc: float = 10.0

    road_trip_charge_limit: float = 100.0
    city_charge_limit: float = 80.0

    minimum_dc_power_kw: float = 100.0
    maximum_detour_km: float = 15.0