from fastapi.testclient import TestClient

from backend.main import app
from backend.services.trip_service import TripService


def sample_trip_response_with_learning():
    return {
        "vehicle": "2024 VinFast VF9 Plus",
        "origin": "Pickering, ON",
        "destination": "Chicago, IL",
        "waypoints": [],
        "route_legs": [
            {
                "leg": 1,
                "origin": "Pickering, ON",
                "destination": "Chicago, IL",
                "distance_km": 859.1,
                "duration_minutes": 577,
                "energy_kwh": 285.0,
                "arrival_soc_without_charging": 0.0,
                "arrival_soc_with_charging": 25.3,
                "charging_required": True,
                "charging_stop_numbers": [
                    1,
                    2
                ]
            }
        ],
        "charging_plan": {
            "charging_required": True,
            "stops": 2,
            "charging_stops": [
                {
                    "stop": 1,
                    "route_leg": 1,
                    "planner_leg": 1,
                    "charger_name": "Test Charger 1",
                    "network": "Test Network",
                    "power_kw": 350.0,
                    "latitude": 42.0,
                    "longitude": -83.0,
                    "route_distance_km": 200.0,
                    "detour_km": 1.0,
                    "detour_minutes": 1.2,
                    "arrival_soc": 15.0,
                    "departure_soc": 80.0,
                    "soc_added": 65.0,
                    "charge_added_kwh": 78.0,
                    "charging_minutes": 39.0,
                    "destination_soc_if_no_more_charging": 0.0,
                    "total_minutes_from_this_stop": 300.0,
                    "score": 650.0,
                    "is_final_stop": False
                },
                {
                    "stop": 2,
                    "route_leg": 1,
                    "planner_leg": 2,
                    "charger_name": "Test Charger 2",
                    "network": "Test Network",
                    "power_kw": 350.0,
                    "latitude": 42.2,
                    "longitude": -85.0,
                    "route_distance_km": 420.0,
                    "detour_km": 0.5,
                    "detour_minutes": 0.6,
                    "arrival_soc": 22.0,
                    "departure_soc": 88.0,
                    "soc_added": 66.0,
                    "charge_added_kwh": 79.2,
                    "charging_minutes": 48.0,
                    "destination_soc_if_no_more_charging": 25.3,
                    "total_minutes_from_this_stop": 210.0,
                    "score": 850.0,
                    "is_final_stop": True
                }
            ],
            "total_charging_minutes": 87.0,
            "total_detour_minutes": 1.8
        },
        "alternative_plans": {
            "available": False,
            "scope": "single_route",
            "plans": [
                {
                    "plan_id": "leg-1-plan-1",
                    "route_leg": 1,
                    "label": "Recommended",
                    "is_recommended": True,
                    "stops": 2,
                    "charging_stops": [
                        {
                            "stop": 1,
                            "route_leg": 1,
                            "planner_leg": 1,
                            "charger_name": "Test Charger 1",
                            "network": "Test Network",
                            "power_kw": 350.0,
                            "latitude": 42.0,
                            "longitude": -83.0,
                            "route_distance_km": 200.0,
                            "detour_km": 1.0,
                            "detour_minutes": 1.2,
                            "arrival_soc": 15.0,
                            "departure_soc": 80.0,
                            "soc_added": 65.0,
                            "charge_added_kwh": 78.0,
                            "charging_minutes": 39.0,
                            "destination_soc_if_no_more_charging": 0.0,
                            "total_minutes_from_this_stop": 300.0,
                            "score": 650.0,
                            "is_final_stop": False
                        },
                        {
                            "stop": 2,
                            "route_leg": 1,
                            "planner_leg": 2,
                            "charger_name": "Test Charger 2",
                            "network": "Test Network",
                            "power_kw": 350.0,
                            "latitude": 42.2,
                            "longitude": -85.0,
                            "route_distance_km": 420.0,
                            "detour_km": 0.5,
                            "detour_minutes": 0.6,
                            "arrival_soc": 22.0,
                            "departure_soc": 88.0,
                            "soc_added": 66.0,
                            "charge_added_kwh": 79.2,
                            "charging_minutes": 48.0,
                            "destination_soc_if_no_more_charging": 25.3,
                            "total_minutes_from_this_stop": 210.0,
                            "score": 850.0,
                            "is_final_stop": True
                        }
                    ],
                    "total_charging_minutes": 87.0,
                    "total_detour_minutes": 1.8,
                    "estimated_total_minutes": 665.8,
                    "final_arrival_soc": 25.3,
                    "planner_cost": 790.0
                }
            ]
        },
        "alternative_plans_by_leg": [
            {
                "route_leg": 1,
                "origin": "Pickering, ON",
                "destination": "Chicago, IL",
                "available": False,
                "recommended_plan_id": "leg-1-plan-1",
                "plans": [
                    {
                        "plan_id": "leg-1-plan-1",
                        "route_leg": 1,
                        "label": "Recommended",
                        "is_recommended": True,
                        "stops": 2,
                        "charging_stops": [
                            {
                                "stop": 1,
                                "route_leg": 1,
                                "planner_leg": 1,
                                "charger_name": "Test Charger 1",
                                "network": "Test Network",
                                "power_kw": 350.0,
                                "latitude": 42.0,
                                "longitude": -83.0,
                                "route_distance_km": 200.0,
                                "detour_km": 1.0,
                                "detour_minutes": 1.2,
                                "arrival_soc": 15.0,
                                "departure_soc": 80.0,
                                "soc_added": 65.0,
                                "charge_added_kwh": 78.0,
                                "charging_minutes": 39.0,
                                "destination_soc_if_no_more_charging": 0.0,
                                "total_minutes_from_this_stop": 300.0,
                                "score": 650.0,
                                "is_final_stop": False
                            },
                            {
                                "stop": 2,
                                "route_leg": 1,
                                "planner_leg": 2,
                                "charger_name": "Test Charger 2",
                                "network": "Test Network",
                                "power_kw": 350.0,
                                "latitude": 42.2,
                                "longitude": -85.0,
                                "route_distance_km": 420.0,
                                "detour_km": 0.5,
                                "detour_minutes": 0.6,
                                "arrival_soc": 22.0,
                                "departure_soc": 88.0,
                                "soc_added": 66.0,
                                "charge_added_kwh": 79.2,
                                "charging_minutes": 48.0,
                                "destination_soc_if_no_more_charging": 25.3,
                                "total_minutes_from_this_stop": 210.0,
                                "score": 850.0,
                                "is_final_stop": True
                            }
                        ],
                        "total_charging_minutes": 87.0,
                        "total_detour_minutes": 1.8,
                        "estimated_total_minutes": 665.8,
                        "final_arrival_soc": 25.3,
                        "planner_cost": 790.0
                    }
                ]
            }
        ],
        "learning": {
            "applied": True,
            "vehicle_id": "vf9",
            "correction_factor": 1.04664,
            "confidence_score": 0.232,
            "observation_count": 1,
            "base_predicted_efficiency": 31.7,
            "learned_predicted_efficiency": 33.179,
            "average_predicted_efficiency_kwh_per_100km": 31.696,
            "average_actual_efficiency_kwh_per_100km": 33.174,
            "average_prediction_error_percent": 4.664
        },
        "summary": {
            "distance_km": 859.1,
            "driving_minutes": 577,
            "charging_minutes": 87.0,
            "detour_minutes": 1.8,
            "total_trip_minutes": 665.8,
            "energy_kwh": 285.0,
            "final_arrival_soc": 25.3,
            "charging_required": True
        }
    }


async def fake_build_trip(
    vehicle_id,
    origin,
    waypoints,
    destination,
    starting_soc,
    average_speed,
    highway_ratio
):
    return sample_trip_response_with_learning()


def test_trip_endpoint_returns_learning_summary(monkeypatch):
    monkeypatch.setattr(
        TripService,
        "build_trip",
        fake_build_trip
    )

    client = TestClient(app)

    response = client.post(
        "/trip/",
        json={
            "vehicle": "vf9",
            "origin": "Pickering, ON",
            "waypoints": [],
            "destination": "Chicago, IL",
            "starting_soc": 100,
            "average_speed": 97,
            "highway_ratio": 0.9
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "learning" in data

    learning = data["learning"]

    assert learning["applied"] is True
    assert learning["vehicle_id"] == "vf9"
    assert learning["correction_factor"] == 1.04664
    assert learning["confidence_score"] == 0.232
    assert learning["observation_count"] == 1
    assert learning["base_predicted_efficiency"] == 31.7
    assert learning["learned_predicted_efficiency"] == 33.179


def test_trip_endpoint_learning_summary_matches_expected_profile(monkeypatch):
    monkeypatch.setattr(
        TripService,
        "build_trip",
        fake_build_trip
    )

    client = TestClient(app)

    response = client.post(
        "/trip/",
        json={
            "vehicle": "vf9",
            "origin": "Pickering, ON",
            "waypoints": [],
            "destination": "Chicago, IL",
            "starting_soc": 100,
            "average_speed": 97,
            "highway_ratio": 0.9
        }
    )

    assert response.status_code == 200

    data = response.json()
    learning = data["learning"]

    assert (
        learning["average_predicted_efficiency_kwh_per_100km"] ==
        31.696
    )

    assert (
        learning["average_actual_efficiency_kwh_per_100km"] ==
        33.174
    )

    assert (
        learning["average_prediction_error_percent"] ==
        4.664
    )