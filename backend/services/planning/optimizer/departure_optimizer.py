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
        arrival_soc,
    ):
        planning = getattr(
            trip,
            "planning",
            None,
        )

        def safe_float(value, default):
            try:
                return float(value)
            except Exception:
                return float(default)

        def unique_sorted(values):
            result = []

            for value in values:
                try:
                    normalized = round(float(value), 1)
                except Exception:
                    continue

                if normalized not in result:
                    result.append(normalized)

            return sorted(result)

        def limit_evenly(values, max_count):
            values = unique_sorted(values)

            if len(values) <= max_count:
                return values

            selected = [values[0]]
            last_index = len(values) - 1

            for slot in range(1, max_count - 1):
                index = round(
                    (last_index * slot)
                    / (max_count - 1)
                )
                selected.append(values[index])

            selected.append(values[-1])

            return unique_sorted(selected)

        target_destination_soc = safe_float(
            getattr(
                planning,
                "target_destination_soc",
                getattr(
                    planning,
                    "destination_target_soc",
                    25.0,
                ),
            ),
            25.0,
        )

        planning_mode = str(
            getattr(
                planning,
                "planning_mode",
                "conservative",
            ) or "conservative"
        ).lower()

        is_fastest = planning_mode in {
            "fastest",
            "abrp",
            "abrp_style",
            "fastest_abrp",
        }

        route = getattr(
            trip,
            "route",
            None,
        )

        route_distance_km = safe_float(
            getattr(
                route,
                "distance_km",
                0.0,
            ) or 0.0,
            0.0,
        )

        arrival_soc = safe_float(
            arrival_soc,
            0.0,
        )

        arrival_soc = max(
            0.0,
            min(
                100.0,
                arrival_soc,
            ),
        )

        if is_fastest:
            safety_buffer_soc = 8.0
            destination_buffer_soc = 5.0
            default_charge_limit_soc = 85.0
            max_option_count = 10
        else:
            safety_buffer_soc = 10.0
            destination_buffer_soc = 10.0
            default_charge_limit_soc = 100.0
            max_option_count = 8

        minimum_departure_soc = max(
            arrival_soc + safety_buffer_soc,
            target_destination_soc + destination_buffer_soc,
        )

        requested_charge_limit_soc = safe_float(
            getattr(
                planning,
                "road_trip_charge_limit",
                default_charge_limit_soc,
            ),
            default_charge_limit_soc,
        )

        if is_fastest:
            soft_charge_cap_soc = min(
                requested_charge_limit_soc,
                85.0,
            )
        else:
            soft_charge_cap_soc = min(
                requested_charge_limit_soc,
                100.0,
            )

        soft_charge_cap_soc = max(
            minimum_departure_soc,
            soft_charge_cap_soc,
        )

        soft_charge_cap_soc = min(
            100.0,
            soft_charge_cap_soc,
        )

        if route_distance_km >= 650:
            step_soc = 5.0
        elif route_distance_km >= 300:
            step_soc = 4.0
        else:
            step_soc = 3.0

        options = [
            minimum_departure_soc,
            soft_charge_cap_soc,
        ]

        current_soc = minimum_departure_soc

        while current_soc <= soft_charge_cap_soc:
            options.append(current_soc)
            current_soc += step_soc

        options.append(
            min(
                100.0,
                minimum_departure_soc + step_soc,
            )
        )

        options.append(
            min(
                100.0,
                minimum_departure_soc + (step_soc * 2),
            )
        )

        clean_options = []

        for option in options:
            option = round(
                max(
                    arrival_soc,
                    min(
                        100.0,
                        soft_charge_cap_soc,
                        float(option),
                    ),
                ),
                1,
            )

            if option <= arrival_soc:
                continue

            clean_options.append(option)

        return limit_evenly(
            clean_options,
            max_option_count,
        )

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
