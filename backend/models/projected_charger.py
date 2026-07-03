from dataclasses import dataclass


@dataclass
class ProjectedCharger:

    name: str

    network: str | None

    latitude: float

    longitude: float

    route_distance_km: float

    detour_distance_km: float

    power_kw: float | None

    supports_vf9: bool