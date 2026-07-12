from backend.services.trip_service import TripService


def test_leg_status_requires_charging_when_soc_is_too_low():
    status = TripService.build_leg_status(
        route_leg_number=2,
        origin="Kingston, ON",
        destination="Cornwall, ON",
        arrival_soc_without_charging=0.0,
        arrival_soc_with_charging=0.0,
        charging_stops=[]
    )

    assert status["charging_required"] is True
    assert status["planning_status"] == "no_feasible_charging_plan_found"
    assert len(status["warnings"]) == 1
    assert "Route leg 2" in status["warnings"][0]


def test_leg_status_is_ok_when_arrival_soc_is_safe():
    status = TripService.build_leg_status(
        route_leg_number=1,
        origin="Pickering, ON",
        destination="Kingston, ON",
        arrival_soc_without_charging=40.2,
        arrival_soc_with_charging=40.2,
        charging_stops=[]
    )

    assert status["charging_required"] is False
    assert status["planning_status"] == "ok"
    assert status["warnings"] == []


def test_leg_status_is_charging_planned_when_stops_exist():
    status = TripService.build_leg_status(
        route_leg_number=1,
        origin="Pickering, ON",
        destination="Ottawa, ON",
        arrival_soc_without_charging=0.0,
        arrival_soc_with_charging=25.0,
        charging_stops=[
            {
                "stop": 1,
                "charger_name": "Test Charger"
            }
        ]
    )

    assert status["charging_required"] is True
    assert status["planning_status"] == "charging_planned"
    assert status["warnings"] == []


def test_trip_planning_status_rolls_up_infeasible_leg():
    status = TripService.build_trip_planning_status(
        [
            {
                "charging_required": False,
                "planning_status": "ok",
                "warnings": []
            },
            {
                "charging_required": True,
                "planning_status": "no_feasible_charging_plan_found",
                "warnings": [
                    "Route leg 2 requires charging but no feasible charging stop was found."
                ]
            }
        ]
    )

    assert status["charging_required"] is True
    assert status["planning_status"] == "incomplete_no_feasible_charging_plan"
    assert len(status["warnings"]) == 1
