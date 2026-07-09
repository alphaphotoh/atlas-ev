from types import SimpleNamespace

from backend.services.trip_service import TripService


def make_charger(
    name="Test Charger",
    network="Test Network",
    power_kw=350,
    latitude=43.0,
    longitude=-79.0,
    route_distance_km=100.0,
    detour_distance_km=2.0
):
    return SimpleNamespace(
        name=name,
        network=network,
        power_kw=power_kw,
        latitude=latitude,
        longitude=longitude,
        route_distance_km=route_distance_km,
        detour_distance_km=detour_distance_km
    )


def make_candidate(
    charger,
    arrival_soc,
    departure_soc,
    destination_arrival_soc,
    charging_time_minutes,
    charge_added_kwh,
    total_trip_time_minutes,
    score
):
    return SimpleNamespace(
        charger=charger,
        arrival_soc=arrival_soc,
        departure_soc=departure_soc,
        destination_arrival_soc=destination_arrival_soc,
        charging_time_minutes=charging_time_minutes,
        charge_added_kwh=charge_added_kwh,
        total_trip_time_minutes=total_trip_time_minutes,
        score=score
    )


def make_leg(number, candidate, route_duration_minutes=438):
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


def make_node(itinerary, final_soc=25.2):
    planning = SimpleNamespace(
        target_destination_soc=25.0
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
        g_cost=0.0
    )


def make_original_trip(duration_minutes=438, arrival_soc=0.0):
    route = SimpleNamespace(
        duration_minutes=duration_minutes
    )

    battery_state = SimpleNamespace(
        soc=arrival_soc
    )

    simulation = SimpleNamespace(
        arrival_soc=arrival_soc
    )

    return SimpleNamespace(
        route=route,
        battery_states=[
            battery_state
        ],
        simulation=simulation
    )


def test_build_charging_stops_returns_expected_stop_details():
    charger = make_charger(
        name="Watertown Hilton Garden Inn",
        network="Shell Recharge Solutions (US)",
        power_kw=351,
        latitude=43.979195639075726,
        longitude=-75.94647830973173,
        route_distance_km=98.5,
        detour_distance_km=2.68
    )

    candidate = make_candidate(
        charger=charger,
        arrival_soc=12.6,
        departure_soc=80.0,
        destination_arrival_soc=0.0,
        charging_time_minutes=39.7,
        charge_added_kwh=80.8,
        total_trip_time_minutes=412.6,
        score=543.1
    )

    leg = make_leg(
        number=1,
        candidate=candidate
    )

    itinerary = make_itinerary(
        legs=[
            leg
        ]
    )

    stops = TripService.build_charging_stops(
        itinerary=itinerary,
        route_leg_number=2,
        start_number=1
    )

    assert len(stops) == 1

    stop = stops[0]

    assert stop["stop"] == 1
    assert stop["route_leg"] == 2
    assert stop["planner_leg"] == 1
    assert stop["charger_name"] == "Watertown Hilton Garden Inn"
    assert stop["network"] == "Shell Recharge Solutions (US)"
    assert stop["power_kw"] == 351
    assert stop["route_distance_km"] == 98.5
    assert stop["detour_km"] == 2.68
    assert stop["detour_minutes"] == 3.2
    assert stop["arrival_soc"] == 12.6
    assert stop["departure_soc"] == 80.0
    assert stop["soc_added"] == 67.4
    assert stop["charge_added_kwh"] == 80.8
    assert stop["charging_minutes"] == 39.7
    assert stop["destination_soc_if_no_more_charging"] == 0.0
    assert stop["total_minutes_from_this_stop"] == 412.6
    assert stop["score"] == 543.1
    assert stop["is_final_stop"] is True


def test_build_charging_stops_numbers_multiple_stops_correctly():
    first_charger = make_charger(
        name="First Charger",
        route_distance_km=100.0,
        detour_distance_km=2.0
    )

    second_charger = make_charger(
        name="Second Charger",
        route_distance_km=250.0,
        detour_distance_km=1.0
    )

    first_candidate = make_candidate(
        charger=first_charger,
        arrival_soc=12.0,
        departure_soc=80.0,
        destination_arrival_soc=0.0,
        charging_time_minutes=40.0,
        charge_added_kwh=80.0,
        total_trip_time_minutes=410.0,
        score=540.0
    )

    second_candidate = make_candidate(
        charger=second_charger,
        arrival_soc=11.0,
        departure_soc=98.0,
        destination_arrival_soc=25.2,
        charging_time_minutes=77.0,
        charge_added_kwh=104.0,
        total_trip_time_minutes=265.0,
        score=300.0
    )

    itinerary = make_itinerary(
        legs=[
            make_leg(
                number=1,
                candidate=first_candidate
            ),
            make_leg(
                number=2,
                candidate=second_candidate
            )
        ]
    )

    stops = TripService.build_charging_stops(
        itinerary=itinerary,
        route_leg_number=2,
        start_number=3
    )

    assert len(stops) == 2

    assert stops[0]["stop"] == 3
    assert stops[0]["charger_name"] == "First Charger"
    assert stops[0]["is_final_stop"] is False

    assert stops[1]["stop"] == 4
    assert stops[1]["charger_name"] == "Second Charger"
    assert stops[1]["is_final_stop"] is True


def test_build_alternative_plans_returns_recommended_and_unique_alternatives():
    first_charger = make_charger(
        name="Watertown Hilton Garden Inn",
        network="Shell Recharge Solutions (US)",
        power_kw=351,
        latitude=43.979195639075726,
        longitude=-75.94647830973173,
        route_distance_km=98.5,
        detour_distance_km=2.68
    )

    second_charger = make_charger(
        name="Pilot Travel Center #494 Rotterdam, NY",
        network="eVgo Network",
        power_kw=350,
        latitude=42.781075308479046,
        longitude=-74.029295606906,
        route_distance_km=253.5,
        detour_distance_km=1.4
    )

    alternative_second_charger = make_charger(
        name="Evolve NY Quackenbush",
        network="Electrify America",
        power_kw=100,
        latitude=42.65321,
        longitude=-73.74811,
        route_distance_km=280.3,
        detour_distance_km=3.55
    )

    recommended_first_candidate = make_candidate(
        charger=first_charger,
        arrival_soc=12.6,
        departure_soc=80.0,
        destination_arrival_soc=0.0,
        charging_time_minutes=39.7,
        charge_added_kwh=80.8,
        total_trip_time_minutes=412.6,
        score=543.1
    )

    recommended_second_candidate = make_candidate(
        charger=second_charger,
        arrival_soc=10.9,
        departure_soc=97.9,
        destination_arrival_soc=25.2,
        charging_time_minutes=77.4,
        charge_added_kwh=104.4,
        total_trip_time_minutes=265.8,
        score=302.24
    )

    alternative_first_candidate = make_candidate(
        charger=first_charger,
        arrival_soc=12.6,
        departure_soc=90.0,
        destination_arrival_soc=0.0,
        charging_time_minutes=55.4,
        charge_added_kwh=92.8,
        total_trip_time_minutes=428.3,
        score=424.6
    )

    alternative_second_candidate = make_candidate(
        charger=alternative_second_charger,
        arrival_soc=13.7,
        departure_soc=91.3,
        destination_arrival_soc=25.0,
        charging_time_minutes=69.4,
        charge_added_kwh=93.1,
        total_trip_time_minutes=247.6,
        score=368.87
    )

    recommended_itinerary = make_itinerary(
        legs=[
            make_leg(
                number=1,
                candidate=recommended_first_candidate
            ),
            make_leg(
                number=2,
                candidate=recommended_second_candidate
            )
        ]
    )

    alternative_itinerary = make_itinerary(
        legs=[
            make_leg(
                number=1,
                candidate=alternative_first_candidate
            ),
            make_leg(
                number=2,
                candidate=alternative_second_candidate
            )
        ]
    )

    recommended_node = make_node(
        itinerary=recommended_itinerary,
        final_soc=25.2
    )

    alternative_node = make_node(
        itinerary=alternative_itinerary,
        final_soc=25.0
    )

    duplicate_recommended_node = make_node(
        itinerary=recommended_itinerary,
        final_soc=25.2
    )

    planning_result = SimpleNamespace(
        recommended=recommended_node,
        completed=[
            recommended_node,
            alternative_node,
            duplicate_recommended_node
        ]
    )

    original_trip = make_original_trip(
        duration_minutes=438,
        arrival_soc=0.0
    )

    plans = TripService.build_alternative_plans(
        planning_result=planning_result,
        route_leg_number=2,
        original_trip=original_trip
    )

    assert len(plans) == 2

    recommended_plan = plans[0]
    alternative_plan = plans[1]

    assert recommended_plan["label"] == "Recommended"
    assert recommended_plan["is_recommended"] is True
    assert recommended_plan["stops"] == 2
    assert recommended_plan["total_charging_minutes"] == 117.1
    assert recommended_plan["total_detour_minutes"] == 4.9
    assert recommended_plan["estimated_total_minutes"] == 560
    assert recommended_plan["final_arrival_soc"] == 25.2

    assert alternative_plan["label"] == "Alternative 2"
    assert alternative_plan["is_recommended"] is False
    assert alternative_plan["stops"] == 2
    assert alternative_plan["total_charging_minutes"] == 124.8
    assert alternative_plan["final_arrival_soc"] == 25.0