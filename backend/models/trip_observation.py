from dataclasses import asdict, dataclass


@dataclass
class TripObservation:
    id: str
    vehicle_id: str
    trip_date: str | None

    origin: str | None
    destination: str | None

    distance_km: float
    starting_soc: float
    ending_soc: float
    charged_energy_kwh: float

    predicted_efficiency_kwh_per_100km: float
    predicted_energy_used_kwh: float

    actual_energy_used_kwh: float
    actual_efficiency_kwh_per_100km: float

    prediction_error_percent: float
    correction_factor: float

    outside_temperature_c: float | None
    average_speed_kmh: float | None
    highway_ratio: float | None

    climate_control: str | None
    tire_pressure_note: str | None
    payload_note: str | None
    notes: str | None

    created_at: str

    def to_dict(self):
        return asdict(self)