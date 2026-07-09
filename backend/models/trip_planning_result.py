from dataclasses import dataclass, field


@dataclass
class TripPlanningResult:
    recommended: object | None = None
    completed: list[object] = field(default_factory=list)