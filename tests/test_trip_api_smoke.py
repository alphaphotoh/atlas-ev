from fastapi.testclient import TestClient

from backend.main import app
from backend.services.trip_service import TripService


def sample_trip_response():
    return {
        "vehicle": "2024 VinFast VF9 Plus",
        "origin": "pickering, on",
        "destination": "Manhattan, New York, NY",
        "waypoints": [
            "Kingston, ON"
        ],
        "route_legs": [
            {
                "leg": 1,
                "origin": "pickering, on",
                "destination": "Kingston, ON",
                "distance_km": 231.0,
                "duration_minutes": 150,
                "energy_kwh": 73.2,
                "arrival_soc_without_charging": 39.7,
                "arrival_soc_with_charging": 39.7,
                "charging_required": False,
                "charging_stop_numbers": []
            },
            {
                "leg": 2,
                "origin": "Kingston, ON",
                "destination": "Manhattan, New York, NY",
                "distance_km": 615.5,
                "duration_minutes": 438,
                "energy_kwh": 195.1,
                "arrival_soc_without_charging": 0.0,
                "arrival_soc_with_charging": 25.2,
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
                    "route_leg": 2,
                    "planner_leg": 1,
                    "charger_name": "Watertown Hilton Garden Inn",
                    "network": "Shell Recharge Solutions (US)",
                    "power_kw": 351,
                    "latitude": 43.979195639075726,
                    "longitude": -75.94647830973173,
                    "route_distance_km": 98.5,
                    "detour_km": 2.68,
                    "detour_minutes": 3.2,
                    "arrival_soc": 12.6,
                    "departure_soc": 80.0,
                    "soc_added": 67.4,
                    "charge_added_kwh": 80.8,
                    "charging_minutes": 39.7,
                    "destination_soc_if_no_more_charging": 0.0,
                    "total_minutes_from_this_stop": 412.6,
                    "score": 543.1,
                    "is_final_stop": False
                },
                {
                    "stop": 2,
                    "route_leg": 2,
                    "planner_leg": 2,
                    "charger_name": "Pilot Travel Center #494 Rotterdam, NY",
                    "network": "eVgo Network",
                    "power_kw": 350,
                    "latitude": 42.781075308479046,
                    "longitude": -74.029295606906,
                    "route_distance_km": 253.5,
                    "detour_km": 1.4,
                    "detour_minutes": 1.7,
                    "arrival_soc": 10.9,
                    "departure_soc": 97.9,
                    "soc_added": 87.0,
                    "charge_added_kwh": 104.4,
                    "charging_minutes": 77.4,
                    "destination_soc_if_no_more_charging": 25.2,
                    "total_minutes_from_this_stop": 265.8,
                    "score": 302.24,
                    "is_final_stop": True
                }
            ],
            "total_charging_minutes": 117.1,
            "total_detour_minutes": 4.9
        },
        "alternative_plans": {
            "available": True,
            "scope": "per_route_leg",
            "plans": [
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
                            "charger_name": "Watertown Hilton Garden Inn",
                            "network": "Shell Recharge Solutions (US)",
                            "power_kw": 351,
                            "latitude": 43.979195639075726,
                            "longitude": -75.94647830973173,
                            "route_distance_km": 98.5,
                            "detour_km": 2.68,
                            "detour_minutes": 3.2,
                            "arrival_soc": 12.6,
                            "departure_soc": 80.0,
                            "soc_added": 67.4,
                            "charge_added_kwh": 80.8,
                            "charging_minutes": 39.7,
                            "destination_soc_if_no_more_charging": 0.0,
                            "total_minutes_from_this_stop": 412.6,
                            "score": 543.1,
                            "is_final_stop": False
                        },
                        {
                            "stop": 2,
                            "route_leg": 2,
                            "planner_leg": 2,
                            "charger_name": "Pilot Travel Center #494 Rotterdam, NY",
                            "network": "eVgo Network",
                            "power_kw": 350,
                            "latitude": 42.781075308479046,
                            "longitude": -74.029295606906,
                            "route_distance_km": 253.5,
                            "detour_km": 1.4,
                            "detour_minutes": 1.7,
                            "arrival_soc": 10.9,
                            "departure_soc": 97.9,
                            "soc_added": 87.0,
                            "charge_added_kwh": 104.4,
                            "charging_minutes": 77.4,
                            "destination_soc_if_no_more_charging": 25.2,
                            "total_minutes_from_this_stop": 265.8,
                            "score": 302.24,
                            "is_final_stop": True
                        }
                    ],
                    "total_charging_minutes": 117.1,
                    "total_detour_minutes": 4.9,
                    "estimated_total_minutes": 559.8,
                    "final_arrival_soc": 25.2,
                    "planner_cost": 685.78
                }
            ]
        },
        "summary": {
            "distance_km": 846.4,
            "driving_minutes": 588,
            "charging_minutes": 117.1,
            "detour_minutes": 4.9,
            "total_trip_minutes": 709.6,
            "energy_kwh": 268.3,
            "final_arrival_soc": 25.2,
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
    return sample_trip_response()


def recommended_plan(data):
    plans = data["alternative_plans"]["plans"]

    recommended = [
        plan
        for plan in plans
        if plan["is_recommended"]
    ]

    assert len(recommended) == 1

    return recommended[0]


def test_trip_endpoint_returns_expected_response_contract(monkeypatch):
    monkeypatch.setattr(
        TripService,
        "build_trip",
        fake_build_trip
    )

    client = TestClient(app)

    response = client.post(
        "/trip/",
        json={
            "vehicle_id": "vf9_plus",
            "origin": "pickering, on",
            "waypoints": [
                "Kingston, ON"
            ],
            "destination": "Manhattan, New York, NY",
            "starting_soc": 100,
            "average_speed": 100,
            "highway_ratio": 0.9
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "route_legs" in data
    assert "charging_plan" in data
    assert "alternative_plans" in data
    assert "summary" in data

    assert isinstance(data["route_legs"], list)
    assert isinstance(data["charging_plan"], dict)
    assert isinstance(data["alternative_plans"], dict)
    assert isinstance(data["summary"], dict)


def test_recommended_plan_matches_main_charging_plan(monkeypatch):
    monkeypatch.setattr(
        TripService,
        "build_trip",
        fake_build_trip
    )

    client = TestClient(app)

    response = client.post(
        "/trip/",
        json={
            "vehicle_id": "vf9_plus",
            "origin": "pickering, on",
            "waypoints": [
                "Kingston, ON"
            ],
            "destination": "Manhattan, New York, NY",
            "starting_soc": 100,
            "average_speed": 100,
            "highway_ratio": 0.9
        }
    )

    assert response.status_code == 200

    data = response.json()

    plan = recommended_plan(data)

    assert plan["charging_stops"] == data["charging_plan"]["charging_stops"]

    assert (
        plan["total_charging_minutes"] ==
        data["charging_plan"]["total_charging_minutes"]
    )

    assert (
        plan["total_detour_minutes"] ==
        data["charging_plan"]["total_detour_minutes"]
    )

    assert (
        plan["stops"] ==
        data["charging_plan"]["stops"]
    )


def test_trip_summary_matches_charging_plan(monkeypatch):
    monkeypatch.setattr(
        TripService,
        "build_trip",
        fake_build_trip
    )

    client = TestClient(app)

    response = client.post(
        "/trip/",
        json={
            "vehicle_id": "vf9_plus",
            "origin": "pickering, on",
            "waypoints": [
                "Kingston, ON"
            ],
            "destination": "Manhattan, New York, NY",
            "starting_soc": 100,
            "average_speed": 100,
            "highway_ratio": 0.9
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["summary"]["charging_minutes"] ==
        data["charging_plan"]["total_charging_minutes"]
    )

    assert (
        data["summary"]["detour_minutes"] ==
        data["charging_plan"]["total_detour_minutes"]
    )

    assert data["summary"]["charging_required"] is True