from dataclasses import dataclass, field


@dataclass
class Charger:

    id: int

    name: str

    address: str

    latitude: float

    longitude: float

    distance_km: float

    power_kw: float | None

    network: str | None

    connectors: list[str] = field(default_factory=list)

    num_connections: int = 0

    supports_vf9: bool = False

    score: int = 0