from dataclasses import dataclass


@dataclass
class SimulationContext:

    predicted_efficiency: float

    energy_needed_kwh: float

    arrival_soc: float

    average_speed: float

    temperature: float

    highway_ratio: float