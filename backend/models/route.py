from dataclasses import dataclass, field

from backend.models.route_segment import RouteSegment


@dataclass
class Route:

    encoded_geometry: str

    geometry: list

    distance_km: float

    duration_minutes: float

    raw: dict

    segments: list[RouteSegment] = field(default_factory=list)