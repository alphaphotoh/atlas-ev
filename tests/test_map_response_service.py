from types import SimpleNamespace

from backend.services.planning.map_response_service import MapResponseService


def build_trip(geometry):
    route = SimpleNamespace(
        geometry=geometry
    )

    return SimpleNamespace(
        route=route
    )


def test_map_response_builds_route_geometry_markers_and_bounds():
    trips = [
        build_trip(
            [
                [-79.1, 43.8],
                [-80.0, 43.7]
            ]
        ),
        build_trip(
            [
                [-80.0, 43.7],
                [-87.6, 41.8]
            ]
        )
    ]

    charging_stops = [
        {
            "stop": 1,
            "route_leg": 1,
            "charger_name": "Test Charger",
            "network": "Test Network",
            "power_kw": 350.0,
            "latitude": 42.5,
            "longitude": -83.1
        }
    ]

    response = MapResponseService.build(
        origin="Pickering, ON",
        waypoints=[
            "Windsor, ON"
        ],
        destination="Chicago, IL",
        trips=trips,
        charging_stops=charging_stops
    )

    assert response["route_geometry_format"] == "longitude_latitude"

    assert response["route_geometry"] == [
        [-79.1, 43.8],
        [-80.0, 43.7],
        [-87.6, 41.8]
    ]

    marker_types = [
        marker["type"]
        for marker in response["markers"]
    ]

    assert marker_types == [
        "origin",
        "waypoint",
        "charger",
        "destination"
    ]

    charger_marker = response["markers"][2]

    assert charger_marker["label"] == "Stop 1: Test Charger"
    assert charger_marker["stop"] == 1
    assert charger_marker["route_leg"] == 1
    assert charger_marker["network"] == "Test Network"
    assert charger_marker["power_kw"] == 350.0

    bounds = response["bounds"]

    assert bounds["min_latitude"] == 41.8
    assert bounds["max_latitude"] == 43.8
    assert bounds["min_longitude"] == -87.6
    assert bounds["max_longitude"] == -79.1


def test_map_response_handles_missing_geometry():
    response = MapResponseService.build(
        origin="Pickering, ON",
        waypoints=[],
        destination="Chicago, IL",
        trips=[],
        charging_stops=[]
    )

    assert response["route_geometry"] == []
    assert response["markers"] == []
    assert response["bounds"] is None