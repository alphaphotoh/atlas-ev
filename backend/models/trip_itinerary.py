from dataclasses import dataclass, field

from backend.models.trip_leg import TripLeg


@dataclass
class TripItinerary:

    legs: list[TripLeg] = field(
        default_factory=list
    )

    total_driving_minutes: float = 0.0

    total_charging_minutes: float = 0.0

    total_detour_minutes: float = 0.0

    total_trip_minutes: float = 0.0

    @property
    def stops(self) -> int:

        return len(
            self.legs
        )

    def recalculate(self):

        self.total_driving_minutes = sum(

            leg.selected_result.driving_time_minutes

            for leg in self.legs

        )

        self.total_charging_minutes = sum(

            leg.selected_result.charging_time_minutes

            for leg in self.legs

        )

        self.total_detour_minutes = sum(

            leg.selected_result.detour_time_minutes

            for leg in self.legs

        )

        self.total_trip_minutes = (

            self.total_driving_minutes +

            self.total_charging_minutes +

            self.total_detour_minutes

        )