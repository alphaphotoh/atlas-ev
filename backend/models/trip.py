from dataclasses import dataclass


@dataclass
class Trip:

    origin: str

    destination: str

    starting_soc: float

    outside_temperature: float