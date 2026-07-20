import asyncio
from backend.services.planning.trip_builder import TripBuilder
from backend.services.simulation.charge_curve import ChargeCurve


class DepartureOptimizer:
    DEFAULT_CURVE = ChargeCurve.default_vf9()

    @staticmethod
    async def optimize(trip, charger, arrival_soc):
        options = await DepartureOptimizer.optimize_options(
            trip=trip,
            charger=charger,
            arrival_soc=arrival_soc,
        )

        if not options:
            return arrival_soc, None

        return options[-1]

    @staticmethod
    async def optimize_options(
        trip,
        charger,
        arrival_soc
    ):
        from backend.services.planning.trip_builder import TripBuilder
        from backend.services.planning.approx_trip_builder import ApproxTripBuilder

        departure_socs = DepartureOptimizer.fast_departure_soc_options(
            trip=trip,
            arrival_soc=arrival_soc,
        )

        route_distance_km = getattr(
            trip.route,
            "distance_km",
            0.0,
        ) or 0.0

        async def build_option(departure_soc):
            try:
                if route_distance_km >= 650:
                    next_trip = ApproxTripBuilder.build_after_charger(
                        trip=trip,
                        charger=charger,
                        departure_soc=departure_soc,
                    )
                else:
                    next_trip = await asyncio.wait_for(
                        TripBuilder.build(
                            trip=trip,
                            charger=charger,
                            departure_soc=departure_soc,
                        ),
                        timeout=8.0,
                    )

                if next_trip is None:
                    return None

                return (
                    departure_soc,
                    next_trip,
                )
            except Exception:
                return None

        results = await asyncio.gather(
            *[
                build_option(departure_soc)
                for departure_soc in departure_socs
            ],
            return_exceptions=True,
        )

        options = []

        for result in results:
            if isinstance(result, Exception):
                continue

            if result is not None:
                options.append(result)

        return options


    @staticmethod
    def fast_departure_soc_options(
        trip,
        arrival_soc
    ):
        planning = getattr(
            trip,
            "planning",
            None,
        )

        target_destination_soc = getattr(
            planning,
            "target_destination_soc",
            25.0,
        )

        route = getattr(
            trip,
            "route",
            None,
        )

        route_distance_km = getattr(
            route,
            "distance_km",
            0.0,
        ) or 0.0

        arrival_soc = float(arrival_soc or 0.0)

        minimum_departure = max(
            arrival_soc + 8.0,
            target_destination_soc + 10.0,
        )

        if route_distance_km >= 650:
            raw_options = [
                100.0,
            ]
        elif route_distance_km >= 300:
            raw_options = [
                minimum_departure,
                85.0,
                100.0,
            ]
        else:
            raw_options = [
                minimum_departure,
                75.0,
                95.0,
            ]

        options = []

        for value in raw_options:
            value = round(
                max(
                    arrival_soc,
                    min(100.0, float(value)),
                ),
                1,
            )

            if value <= arrival_soc:
                continue

            if value not in options:
                options.append(value)

        return options[:3]


    @staticmethod
    async def non_final_options(
        trip,
        charger,
        arrival_soc,
        low_soc,
        limit_soc,
    ):
        planning = trip.planning

        cap_soc = DepartureOptimizer.non_final_cap_soc(
            trip=trip,
            charger=charger,
            arrival_soc=arrival_soc,
            limit_soc=limit_soc,
        )

        cap_soc = max(
            cap_soc,
            low_soc
        )

        levels = DepartureOptimizer.non_final_candidate_levels(
            low_soc=low_soc,
            cap_soc=cap_soc,
            planning=planning,
        )

        options = []

        for departure_soc in levels:
            next_trip = await TripBuilder.build(
                trip=trip,
                charger=charger,
                departure_soc=departure_soc,
            )

            options.append(
                (
                    departure_soc,
                    next_trip,
                )
            )

        return options

    @staticmethod
    def non_final_candidate_levels(
        low_soc,
        cap_soc,
        planning,
    ):
        base_levels = [
            low_soc,
            60.0,
            70.0,
            75.0,
            80.0,
            cap_soc,
        ]

        default_non_final_cap = getattr(
            planning,
            "non_final_charge_cap_soc",
            85.0
        )

        if cap_soc >= 85.0:
            base_levels.append(
                85.0
            )

        if cap_soc > default_non_final_cap:
            base_levels.extend(
                [
                    90.0,
                    95.0,
                    cap_soc,
                ]
            )

        levels = []

        for level in base_levels:
            if level < low_soc:
                continue

            if level > cap_soc:
                continue

            levels.append(
                DepartureOptimizer.round_soc(
                    level
                )
            )

        return sorted(
            set(levels)
        )

    @staticmethod
    async def final_destination_option(
        trip,
        charger,
        low_soc,
        high_soc,
        target_soc,
        high_trip,
    ):
        planning = trip.planning

        precision = getattr(
            planning,
            "soc_optimization_precision",
            0.5
        )

        best_soc = high_soc
        best_trip = high_trip

        while (
            high_soc -
            low_soc
        ) > precision:
            mid_soc = DepartureOptimizer.round_soc(
                (
                    low_soc +
                    high_soc
                ) / 2.0
            )

            mid_trip = await TripBuilder.build(
                trip=trip,
                charger=charger,
                departure_soc=mid_soc,
            )

            mid_destination_soc = DepartureOptimizer.destination_soc(
                mid_trip,
            )

            if mid_destination_soc >= target_soc:
                best_soc = mid_soc
                best_trip = mid_trip
                high_soc = mid_soc
            else:
                low_soc = mid_soc

        return [
            (
                DepartureOptimizer.round_soc(
                    best_soc
                ),
                best_trip,
            )
        ]

    @staticmethod
    def non_final_cap_soc(
        trip,
        charger,
        arrival_soc,
        limit_soc,
    ):
        planning = trip.planning

        efficient_cap = DepartureOptimizer.DEFAULT_CURVE.efficient_soc_cap(
            vehicle=trip.vehicle,
            charger=charger,
            planning=planning,
            arrival_soc=arrival_soc,
            limit_soc=limit_soc,
        )

        buffer_soc = DepartureOptimizer.reliability_buffer_soc(
            trip=trip,
            charger=charger,
            planning=planning,
        )

        return min(
            limit_soc,
            efficient_cap + buffer_soc
        )

    @staticmethod
    def reliability_buffer_soc(
        trip,
        charger,
        planning,
    ):
        buffer_soc = 0.0

        is_sparse = (
            getattr(
                trip,
                "is_sparse_route",
                False
            )
            or
            getattr(
                charger,
                "is_sparse_route",
                False
            )
            or
            getattr(
                charger,
                "sparse_route",
                False
            )
        )

        if is_sparse:
            buffer_soc += getattr(
                planning,
                "sparse_route_buffer_soc",
                12.0
            )

        reliability_score = getattr(
            charger,
            "reliability_score",
            None
        )

        if reliability_score is not None:
            threshold = getattr(
                planning,
                "low_reliability_threshold",
                0.5
            )

            if reliability_score < threshold:
                buffer_soc += getattr(
                    planning,
                    "reliability_buffer_soc",
                    12.0
                )

        return buffer_soc

    @staticmethod
    def destination_target_soc(trip):
        planning = trip.planning

        return getattr(
            planning,
            "target_destination_soc",
            getattr(
                planning,
                "destination_target_soc",
                25.0
            )
        )

    @staticmethod
    def limit_soc(planning):
        return DepartureOptimizer.round_soc(
            getattr(
                planning,
                "road_trip_charge_limit",
                100.0
            )
        )

    @staticmethod
    def destination_soc(trip):
        if not trip:
            return 0.0

        if getattr(trip, "battery_states", None):
            return trip.battery_states[-1].soc

        simulation = getattr(
            trip,
            "simulation",
            None
        )

        if simulation is not None:
            return simulation.arrival_soc or 0.0

        return 0.0

    @staticmethod
    def round_soc(soc):
        return round(
            max(
                0.0,
                min(
                    100.0,
                    float(soc or 0.0)
                )
            ),
            1
        )