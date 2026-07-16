from types import SimpleNamespace

from backend.services.routing.route_segment_service import (
    RouteSegmentService,
)


def test_builds_segments_from_geometry_when_route_segments_missing():
    route = SimpleNamespace(
        distance_km=100,
        duration_minutes=60,
        geometry=[
            [-79.0, 43.0],
            [-78.5, 43.2],
            [-78.0, 43.4]
        ],
        segments=[]
    )

    segments = RouteSegmentService.segments_for_route(
        route
    )

    assert len(segments) == 2
    assert round(
        sum(segment.length_km for segment in segments),
        1
    ) == 100.0
    assert round(
        sum(segment.duration_minutes for segment in segments),
        1
    ) == 60.0
    assert round(
        segments[-1].cumulative_distance_km,
        1
    ) == 100.0


def test_sample_points_include_start_middle_and_end():
    route = SimpleNamespace(
        distance_km=60,
        duration_minutes=60,
        geometry=[
            [-79.0, 43.0],
            [-78.5, 43.2],
            [-78.0, 43.4]
        ],
        segments=[]
    )

    points = RouteSegmentService.sample_points(
        route=route,
        spacing_km=25
    )

    assert len(points) == 4
    assert points[0]["distance_km"] == 0.0
    assert points[1]["distance_km"] == 25
    assert points[2]["distance_km"] == 50
    assert points[3]["distance_km"] == 60


def test_coordinate_at_distance_returns_end_for_route_distance():
    route = SimpleNamespace(
        distance_km=100,
        duration_minutes=60,
        geometry=[
            [-79.0, 43.0],
            [-78.0, 44.0]
        ],
        segments=[]
    )

    coordinate = RouteSegmentService.coordinate_at_distance(
        route=route,
        distance_km=100
    )

    assert coordinate == [-78.0, 44.0]