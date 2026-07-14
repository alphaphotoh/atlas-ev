from dataclasses import dataclass


@dataclass
class TripPlanningConfig:
    #
    # Intermediate charger arrival floor.
    # This is a low safety floor only.
    #
    minimum_charger_arrival_soc: float = 10.0
    min_arrival_soc: float = 10.0

    #
    # Soft preferred arrival band at charging stops.
    # Used for scoring/sorting only, not as a hard floor.
    #
    ideal_charger_arrival_soc_min: float = 10.0
    ideal_charger_arrival_soc_max: float = 30.0

    #
    # Final destination target.
    # Keep target_destination_soc for compatibility with existing code.
    #
    target_destination_soc: float = 25.0
    destination_target_soc: float = 25.0
    destination_target_min_soc: float = 20.0
    destination_target_max_soc: float = 30.0

    safety_buffer_soc: float = 10.0

    #
    # Charge limits.
    #
    road_trip_charge_limit: float = 100.0
    city_charge_limit: float = 80.0

    #
    # Curve-aware optimization.
    #
    non_final_charge_cap_soc: float = 85.0
    near_peak_start_soc: float = 10.0
    near_peak_end_soc: float = 70.0
    marginal_cost_multiplier: float = 2.0
    soc_optimization_precision: float = 0.5

    #
    # Reliability / sparse route hedge.
    #
    reliability_buffer_soc: float = 12.0
    sparse_route_buffer_soc: float = 12.0
    low_reliability_threshold: float = 0.5

    #
    # Charger filtering.
    #
    minimum_dc_power_kw: float = 100.0
    maximum_detour_km: float = 15.0