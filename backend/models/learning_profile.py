from dataclasses import asdict, dataclass


@dataclass
class LearningProfile:
    vehicle_id: str

    observation_count: int
    total_distance_km: float

    average_predicted_efficiency_kwh_per_100km: float
    average_actual_efficiency_kwh_per_100km: float

    correction_factor: float
    average_prediction_error_percent: float

    confidence_score: float

    last_observation_id: str | None
    updated_at: str | None

    def to_dict(self):
        return asdict(self)