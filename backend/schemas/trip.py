from pydantic import BaseModel


class TripRequest(BaseModel):

    vehicle: str = "vf9"

    origin: str

    destination: str

    waypoints: list[str] = []

    starting_soc: float

    average_speed: float = 110

    highway_ratio: float = 0.8