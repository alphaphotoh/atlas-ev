import pytest

from pydantic import ValidationError

from backend.schemas.trip_response import TripResponse


def validate_trip_response(data):
    if hasattr(TripResponse, "model_validate"):
        return TripResponse.model_validate(data)

    return TripResponse.parse_obj(data)


def valid_trip_response():
    return {
        "vehicle": "2024 VinFast VF9 Plus",
        "origin": "pickering, on",
        "destination": "chicago, IL, USA",
        "waypoints": [
            "windsor, on"
        ],
        "route_legs": [
            {
                "leg": 1,
                "origin": "pickering, on",
                "destination": "windsor, on",
                "distance_km": 396.3,
                "duration_minutes": 268,
                "energy_kwh": 125.6,
                "arrival_soc_without_charging": 0.0,
                "arrival_soc_with_charging": 25.1,
                "charging_required": True,
                "charging_stop_numbers": [
                    1
                ]
            },
            {
                "leg": 2,
                "origin": "windsor, on",
                "destination": "chicago, IL, USA",
                "distance_km": 462.8,
                "duration_minutes": 310,
                "energy_kwh": 146.7,
                "arrival_soc_without_charging": 0.0,
                "arrival_soc_with_charging": 25.3,
                "charging_required": True,
                "charging_stop_numbers": [
                    2,
                    3
                ]
            }
        ],
        "charging_plan": {
            "charging_required": True,
            "stops": 3,
            "charging_stops": [
                {
                    "stop": 1,
                    "route_leg": 1,
                    "planner_leg": 1,
                    "charger_name": "Ivy - ONRoute West Lorne",
                    "network": "IVY",
                    "power_kw": 100.0,
                    "latitude": 42.649829795612845,
                    "longitude": -81.55617422242784,
                    "route_distance_km": 258.3,
                    "detour_km": 0.08,
                    "detour_minutes": 0.1,
                    "arrival_soc": 30.1,
                    "departure_soc": 62.5,
                    "soc_added": 32.4,
                    "charge_added_kwh": 38.8,
                    "charging_minutes": 23.4,
                    "destination_soc_if_no_more_charging": 25.1,
                    "total_minutes_from_this_stop": 117.6,
                    "score": 915.97,
                    "is_final_stop": True
                },
                {
                    "stop": 2,
                    "route_leg": 2,
                    "planner_leg": 1,
                    "charger_name": "Livonia Commons",
                    "network": "eVgo Network",
                    "power_kw": 350.0,
                    "latitude": 42.38090779213289,
                    "longitude": -83.33416596834041,
                    "route_distance_km": 36.3,
                    "detour_km": 0.29,
                    "detour_minutes": 0.3,
                    "arrival_soc": 15.0,
                    "departure_soc": 80.0,
                    "soc_added": 65.0,
                    "charge_added_kwh": 78.0,
                    "charging_minutes": 39.2,
                    "destination_soc_if_no_more_charging": 0.0,
                    "total_minutes_from_this_stop": 318.1,
                    "score": 652.81,
                    "is_final_stop": False
                },
                {
                    "stop": 3,
                    "route_leg": 2,
                    "planner_leg": 2,
                    "charger_name": "West Michigan International",
                    "network": "EV Connect",
                    "power_kw": 350.0,
                    "latitude": 42.2388548195737,
                    "longitude": -85.6892128793697,
                    "route_distance_km": 204.8,
                    "detour_km": 0.11,
                    "detour_minutes": 0.1,
                    "arrival_soc": 22.9,
                    "departure_soc": 88.0,
                    "soc_added": 65.1,
                    "charge_added_kwh": 78.1,
                    "charging_minutes": 47.7,
                    "destination_soc_if_no_more_charging": 25.3,
                    "total_minutes_from_this_stop": 205.8,
                    "score": 853.0,
                    "is_final_stop": True
                }
            ],
            "total_charging_minutes": 110.3,
            "total_detour_minutes": 0.5
        },
        "alternative_plans": {
            "available": True,
            "scope": "per_route_leg",
            "plans": [
                {
                    "plan_id": "leg-1-plan-1",
                    "route_leg": 1,
                    "label": "Recommended",
                    "is_recommended": True,
                    "stops": 1,
                    "charging_stops": [
                        {
                            "stop": 1,
                            "route_leg": 1,
                            "planner_leg": 1,
                            "charger_name": "Ivy - ONRoute West Lorne",
                            "network": "IVY",
                            "power_kw": 100.0,
                            "latitude": 42.649829795612845,
                            "longitude": -81.55617422242784,
                            "route_distance_km": 258.3,
                            "detour_km": 0.08,
                            "detour_minutes": 0.1,
                            "arrival_soc": 30.1,
                            "departure_soc": 62.5,
                            "soc_added": 32.4,
                            "charge_added_kwh": 38.8,
                            "charging_minutes": 23.4,
                            "destination_soc_if_no_more_charging": 25.1,
                            "total_minutes_from_this_stop": 117.6,
                            "score": 915.97,
                            "is_final_stop": True
                        }
                    ],
                    "total_charging_minutes": 23.4,
                    "total_detour_minutes": 0.1,
                    "estimated_total_minutes": 291.2,
                    "final_arrival_soc": 25.1,
                    "planner_cost": 351.26
                },
                {
                    "plan_id": "leg-2-plan-1",
                    "route_leg": 2,
                    "label": "Recommended",
                    "is_recommended": True,
                    "stops": 2,
                    "charging_stops": [
                        {
                            "stop": 1,
                            "route_leg": 2,
                            "planner_leg": 1,
                            "charger_name": "Livonia Commons",
                            "network": "eVgo Network",
                            "power_kw": 350.0,
                            "latitude": 42.38090779213289,
                            "longitude": -83.33416596834041,
                            "route_distance_km": 36.3,
                            "detour_km": 0.29,
                            "detour_minutes": 0.3,
                            "arrival_soc": 15.0,
                            "departure_soc": 80.0,
                            "soc_added": 65.0,
                            "charge_added_kwh": 78.0,
                            "charging_minutes": 39.2,
                            "destination_soc_if_no_more_charging": 0.0,
                            "total_minutes_from_this_stop": 318.1,
                            "score": 652.81,
                            "is_final_stop": False
                        },
                        {
                            "stop": 2,
                            "route_leg": 2,
                            "planner_leg": 2,
                            "charger_name": "West Michigan International",
                            "network": "EV Connect",
                            "power_kw": 350.0,
                            "latitude": 42.2388548195737,
                            "longitude": -85.6892128793697,
                            "route_distance_km": 204.8,
                            "detour_km": 0.11,
                            "detour_minutes": 0.1,
                            "arrival_soc": 22.9,
                            "departure_soc": 88.0,
                            "soc_added": 65.1,
                            "charge_added_kwh": 78.1,
                            "charging_minutes": 47.7,
                            "destination_soc_if_no_more_charging": 25.3,
                            "total_minutes_from_this_stop": 205.8,
                            "score": 853.0,
                            "is_final_stop": True
                        }
                    ],
                    "total_charging_minutes": 86.9,
                    "total_detour_minutes": 0.4,
                    "estimated_total_minutes": 396.9,
                    "final_arrival_soc": 25.3,
                    "planner_cost": 517.21
                }
            ]
        },
        "summary": {
            "distance_km": 859.1,
            "driving_minutes": 577,
            "charging_minutes": 110.3,
            "detour_minutes": 0.5,
            "total_trip_minutes": 688.1,
            "energy_kwh": 272.3,
            "final_arrival_soc": 25.3,
            "charging_required": True
        }
    }


def test_trip_response_schema_accepts_valid_trip_response():
    data = valid_trip_response()

    response = validate_trip_response(data)

    assert response.vehicle == "2024 VinFast VF9 Plus"
    assert response.origin == "pickering, on"
    assert response.destination == "chicago, IL, USA"
    assert len(response.route_legs) == 2
    assert response.charging_plan.stops == 3
    assert response.alternative_plans.available is True
    assert response.summary.final_arrival_soc == 25.3


def test_trip_response_schema_allows_optional_weather_fields_to_be_missing():
    data = valid_trip_response()

    response = validate_trip_response(data)

    assert response.weather is None
    assert response.route_weather is None
    assert response.efficiency_profile is None


def test_trip_response_schema_rejects_missing_charging_plan():
    data = valid_trip_response()

    del data["charging_plan"]

    with pytest.raises(ValidationError):
        validate_trip_response(data)


def test_trip_response_schema_rejects_invalid_stop_count_type():
    data = valid_trip_response()

    data["charging_plan"]["stops"] = "three"

    with pytest.raises(ValidationError):
        validate_trip_response(data)


def test_trip_response_schema_rejects_missing_required_charger_name():
    data = valid_trip_response()

    del data["charging_plan"]["charging_stops"][0]["charger_name"]

    with pytest.raises(ValidationError):
        validate_trip_response(data)