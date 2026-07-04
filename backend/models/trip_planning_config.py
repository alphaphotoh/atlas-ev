from dataclasses import dataclass


@dataclass
class TripPlanningConfig:

    # Minimum SOC when arriving at any charger
    minimum_charger_arrival_soc: float = 25.0

    # Minimum SOC when arriving at destination
    target_destination_soc: float = 25.0

    # Maximum SOC to charge to on road trips
    road_trip_charge_limit: float = 100.0

    # Maximum SOC for normal daily charging
    city_charge_limit: float = 80.0

    # Ignore chargers below this power
    minimum_dc_power_kw: float = 100.0

    # Ignore chargers farther than this from the route
    maximum_detour_km: float = 5.0