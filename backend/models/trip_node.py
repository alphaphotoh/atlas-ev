from dataclasses import dataclass, field

from backend.models.trip_plan import TripPlan
from backend.models.trip_itinerary import TripItinerary


@dataclass
class TripNode:

    trip: TripPlan

    itinerary: TripItinerary = field(
        default_factory=TripItinerary
    )

    depth: int = 0

    parent: "TripNode | None" = None

    score: float = 0.0

    g_cost: float = 0.0