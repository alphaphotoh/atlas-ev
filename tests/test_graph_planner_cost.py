from types import SimpleNamespace

from backend.services.planning.graph_planner import GraphPlanner


def make_charger(
    name,
    detour_distance_km
):
    return SimpleNamespace(
        name=name,
        detour_distance_km=detour_distance_km,
        latitude=43.0,
        longitude=-79.0
    )


def make_candidate(
    charger,
    arrival_soc,
    departure_soc,
    charging_time_minutes,
    score=500.0
):
    return SimpleNamespace(
        charger=charger,
        arrival_soc=arrival_soc,
        departure_soc=departure_soc,
        charging_time_minutes=charging_time_minutes,
        score=score
    )


def make_leg(
    number,
    candidate,
    route_duration_minutes=438.0
):
    route = SimpleNamespace(
        duration_minutes=route_duration_minutes
    )

    return SimpleNamespace(
        number=number,
        route=route,
        selected_result=candidate
    )


def make_itinerary(legs):
    return SimpleNamespace(
        legs=legs
    )


def make_node(
    itinerary,
    final_soc=25.2,
    target_soc=25.0,
    g_cost=0.0
):
    planning = SimpleNamespace(
        target_destination_soc=target_soc
    )

    battery_state = SimpleNamespace(
        soc=final_soc
    )

    trip = SimpleNamespace(
        planning=planning,
        battery_states=[
            battery_state
        ]
    )

    return SimpleNamespace(
        itinerary=itinerary,
        trip=trip,
        g_cost=g_cost
    )


def test_itinerary_cost_prefers_lower_total_trip_time():
    watertown = make_charger(
        name="Watertown Hilton Garden Inn",
        detour_distance_km=2.68
    )

    pilot = make_charger(
        name="Pilot Travel Center #494 Rotterdam, NY",
        detour_distance_km=1.4
    )

    evolve = make_charger(
        name="Evolve NY Quackenbush",
        detour_distance_km=3.55
    )

    faster_plan = make_node(
        itinerary=make_itinerary(
            legs=[
                make_leg(
                    number=1,
                    candidate=make_candidate(
                        charger=watertown,
                        arrival_soc=12.6,
                        departure_soc=80.0,
                        charging_time_minutes=39.7,
                        score=543.1
                    )
                ),
                make_leg(
                    number=2,
                    candidate=make_candidate(
                        charger=pilot,
                        arrival_soc=10.9,
                        departure_soc=97.9,
                        charging_time_minutes=77.4,
                        score=302.24
                    )
                )
            ]
        ),
        final_soc=25.2
    )

    slower_plan = make_node(
        itinerary=make_itinerary(
            legs=[
                make_leg(
                    number=1,
                    candidate=make_candidate(
                        charger=watertown,
                        arrival_soc=12.6,
                        departure_soc=90.0,
                        charging_time_minutes=55.4,
                        score=424.6
                    )
                ),
                make_leg(
                    number=2,
                    candidate=make_candidate(
                        charger=evolve,
                        arrival_soc=13.7,
                        departure_soc=91.3,
                        charging_time_minutes=69.4,
                        score=368.87
                    )
                )
            ]
        ),
        final_soc=25.0
    )

    faster_cost = GraphPlanner.itinerary_cost(
        faster_plan
    )

    slower_cost = GraphPlanner.itinerary_cost(
        slower_plan
    )

    assert faster_cost < slower_cost


def test_itinerary_cost_penalizes_full_charge_when_otherwise_similar():
    charger = make_charger(
        name="Test Charger",
        detour_distance_km=1.0
    )

    normal_charge_plan = make_node(
        itinerary=make_itinerary(
            legs=[
                make_leg(
                    number=1,
                    candidate=make_candidate(
                        charger=charger,
                        arrival_soc=20.0,
                        departure_soc=95.0,
                        charging_time_minutes=50.0,
                        score=500.0
                    )
                )
            ]
        ),
        final_soc=25.0
    )

    full_charge_plan = make_node(
        itinerary=make_itinerary(
            legs=[
                make_leg(
                    number=1,
                    candidate=make_candidate(
                        charger=charger,
                        arrival_soc=20.0,
                        departure_soc=100.0,
                        charging_time_minutes=50.0,
                        score=500.0
                    )
                )
            ]
        ),
        final_soc=25.0
    )

    normal_cost = GraphPlanner.itinerary_cost(
        normal_charge_plan
    )

    full_cost = GraphPlanner.itinerary_cost(
        full_charge_plan
    )

    assert full_cost > normal_cost


def test_itinerary_cost_heavily_penalizes_destination_soc_shortfall():
    charger = make_charger(
        name="Test Charger",
        detour_distance_km=1.0
    )

    complete_plan = make_node(
        itinerary=make_itinerary(
            legs=[
                make_leg(
                    number=1,
                    candidate=make_candidate(
                        charger=charger,
                        arrival_soc=20.0,
                        departure_soc=90.0,
                        charging_time_minutes=50.0,
                        score=500.0
                    )
                )
            ]
        ),
        final_soc=25.0
    )

    incomplete_plan = make_node(
        itinerary=make_itinerary(
            legs=[
                make_leg(
                    number=1,
                    candidate=make_candidate(
                        charger=charger,
                        arrival_soc=20.0,
                        departure_soc=90.0,
                        charging_time_minutes=50.0,
                        score=500.0
                    )
                )
            ]
        ),
        final_soc=20.0
    )

    complete_cost = GraphPlanner.itinerary_cost(
        complete_plan
    )

    incomplete_cost = GraphPlanner.itinerary_cost(
        incomplete_plan
    )

    assert incomplete_cost > complete_cost + 1000.0


def test_sorted_completed_places_best_cost_first():
    watertown = make_charger(
        name="Watertown Hilton Garden Inn",
        detour_distance_km=2.68
    )

    pilot = make_charger(
        name="Pilot Travel Center #494 Rotterdam, NY",
        detour_distance_km=1.4
    )

    slower_plan = make_node(
        itinerary=make_itinerary(
            legs=[
                make_leg(
                    number=1,
                    candidate=make_candidate(
                        charger=watertown,
                        arrival_soc=12.6,
                        departure_soc=90.0,
                        charging_time_minutes=55.4,
                        score=424.6
                    )
                ),
                make_leg(
                    number=2,
                    candidate=make_candidate(
                        charger=pilot,
                        arrival_soc=20.9,
                        departure_soc=97.9,
                        charging_time_minutes=73.4,
                        score=557.33
                    )
                )
            ]
        ),
        final_soc=25.2
    )

    faster_plan = make_node(
        itinerary=make_itinerary(
            legs=[
                make_leg(
                    number=1,
                    candidate=make_candidate(
                        charger=watertown,
                        arrival_soc=12.6,
                        departure_soc=80.0,
                        charging_time_minutes=39.7,
                        score=543.1
                    )
                ),
                make_leg(
                    number=2,
                    candidate=make_candidate(
                        charger=pilot,
                        arrival_soc=10.9,
                        departure_soc=97.9,
                        charging_time_minutes=77.4,
                        score=302.24
                    )
                )
            ]
        ),
        final_soc=25.2
    )

    sorted_nodes = GraphPlanner.sorted_completed(
        [
            slower_plan,
            faster_plan
        ]
    )

    assert sorted_nodes[0] is faster_plan
    assert sorted_nodes[1] is slower_plan