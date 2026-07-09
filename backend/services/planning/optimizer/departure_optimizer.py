from backend.services.planning.trip_builder import TripBuilder


class DepartureOptimizer:
    PRECISION_SOC = 0.5

    @staticmethod
    async def optimize(trip, charger, arrival_soc):
        target_soc = trip.planning.target_destination_soc
        limit_soc = trip.planning.road_trip_charge_limit

        low_soc = max(
            arrival_soc,
            trip.planning.ideal_charger_arrival_soc_min
        )

        low_soc = min(low_soc, limit_soc)
        low_soc = round(low_soc, 1)
        high_soc = round(limit_soc, 1)

        low_trip = await TripBuilder.build(
            trip=trip,
            charger=charger,
            departure_soc=low_soc
        )

        if DepartureOptimizer.destination_soc(low_trip) >= target_soc:
            return low_soc, low_trip

        high_trip = await TripBuilder.build(
            trip=trip,
            charger=charger,
            departure_soc=high_soc
        )

        if DepartureOptimizer.destination_soc(high_trip) < target_soc:
            return high_soc, high_trip

        best_soc = high_soc
        best_trip = high_trip

        while (high_soc - low_soc) > DepartureOptimizer.PRECISION_SOC:
            mid_soc = round(
                (low_soc + high_soc) / 2,
                1
            )

            mid_trip = await TripBuilder.build(
                trip=trip,
                charger=charger,
                departure_soc=mid_soc
            )

            mid_destination_soc = DepartureOptimizer.destination_soc(
                mid_trip
            )

            if mid_destination_soc >= target_soc:
                best_soc = mid_soc
                best_trip = mid_trip
                high_soc = mid_soc
            else:
                low_soc = mid_soc

        return round(best_soc, 1), best_trip

    @staticmethod
    def destination_soc(trip):
        if not trip.battery_states:
            return 0.0

        return trip.battery_states[-1].soc