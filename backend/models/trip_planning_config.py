from dataclasses import dataclass


@dataclass
class TripPlanningConfig:

    # Minimum SOC when arriving at any charger
    minimum_charger_arrival_soc: float = 25.0

    # Minimum SOC when arriving at destination
    target_destination_soc: float = 25.0

    # Safety reserve added to calculated departure SOC
    safety_buffer_soc: float = 10.0

    # Road trip charging limit
    road_trip_charge_limit: float = 100.0

    # Normal daily charging limit
    city_charge_limit: float = 80.0

    # Ignore chargers below this power
    minimum_dc_power_kw: float = 100.0

    # Ignore chargers farther than this from the route
    maximum_detour_km: float = 5.0