from dataclasses import dataclass, field

from backend.models.trip_leg import TripLeg


@dataclass
class TripItinerary:

    legs: list[TripLeg] = field(
        default_factory=list
    )

    total_charging_minutes: float = 0.0

    total_trip_minutes: float = 0.0

    @property
    def stops(self) -> int:

        return len(
            self.legs
        )

    @property
    def last_leg(self) -> TripLeg | None:

        if not self.legs:

            return None

        return self.legs[-1]

    @property
    def destination_soc(self) -> float:

        if not self.last_leg:

            return 0.0

        return (
            self.last_leg
            .selected_result
            .destination_arrival_soc
        )

    @property
    def completed(self) -> bool:

        if not self.last_leg:

            return False

        return (
            self.destination_soc >=
            25.0
        )

    def add_leg(
        self,
        leg: TripLeg
    ):

        self.legs.append(
            leg
        )

        self.recalculate()

    def recalculate(self):

        self.total_charging_minutes = sum(

            leg.selected_result.charging_time_minutes

            for leg in self.legs

        )

        self.total_trip_minutes = sum(

            leg.selected_result.total_trip_time_minutes

            for leg in self.legs

        )