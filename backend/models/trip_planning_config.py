from dataclasses import dataclass


@dataclass
class TripPlanningConfig:

    #
    # Hard minimum SOC allowed when arriving
    # at any charging stop.
    #
    minimum_charger_arrival_soc: float = 5.0

    #
    # Preferred arrival SOC range.
    #
    ideal_charger_arrival_soc_min: float = 23.0

    ideal_charger_arrival_soc_max: float = 31.0

    #
    # Minimum SOC required at the destination.
    #
    target_destination_soc: float = 25.0

    #
    # Maximum SOC to charge to on road trips.
    #
    road_trip_charge_limit: float = 100.0

    #
    # Daily charging limit.
    #
    city_charge_limit: float = 80.0

    #
    # Ignore chargers slower than this.
    #
    minimum_dc_power_kw: float = 100.0

    #
    # Ignore chargers farther than this from
    # the route.
    #
    maximum_detour_km: float = 5.0