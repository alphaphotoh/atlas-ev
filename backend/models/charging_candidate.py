from dataclasses import dataclass

from backend.models.charger import Charger


@dataclass
class ChargingCandidate:

    charger: Charger

    arrival_soc: float

    departure_soc: float = 0

    charging_minutes: float = 0

    score: float = 0