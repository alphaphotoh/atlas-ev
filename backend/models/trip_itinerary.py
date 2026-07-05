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
            .destination_soc
        )

    @property
    def completed(self) -> bool:

        return (

            self.last_leg is not None

            and

            not self.last_leg.selected_result.requires_additional_stop

        )

    @property
    def requires_additional_stop(self) -> bool:

        if not self.last_leg:

            return False

        return (
            self.last_leg
            .selected_result
            .requires_additional_stop
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