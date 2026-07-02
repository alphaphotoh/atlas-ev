from backend.models.vehicles.vf9 import VF9


class VehicleRegistry:

    _vehicles = {
        "vf9": VF9,
    }

    @classmethod
    def get(cls, vehicle_id: str):

        vehicle = cls._vehicles.get(vehicle_id.lower())

        if vehicle is None:
            raise ValueError(f"Unknown vehicle '{vehicle_id}'")

        return vehicle

    @classmethod
    def list(cls):
        return list(cls._vehicles.keys())