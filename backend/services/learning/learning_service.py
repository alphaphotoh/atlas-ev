from datetime import datetime, timezone
from uuid import uuid4

from backend.models.learning_profile import LearningProfile
from backend.models.registry import VehicleRegistry
from backend.models.trip_observation import TripObservation
from backend.services.learning.learning_repository import LearningRepository


class LearningService:
    @staticmethod
    def upload_trip(request):
        vehicle = LearningService.get_vehicle(
            request.vehicle_id
        )

        actual_energy_used_kwh = LearningService.calculate_actual_energy_used(
            request=request,
            vehicle=vehicle
        )

        predicted_energy_used_kwh = LearningService.calculate_predicted_energy_used(
            request=request
        )

        actual_efficiency = (
            actual_energy_used_kwh /
            request.distance_km
        ) * 100

        predicted_efficiency = (
            request.predicted_efficiency_kwh_per_100km
        )

        correction_factor = (
            actual_efficiency /
            predicted_efficiency
        )

        prediction_error_percent = (
            (
                actual_efficiency -
                predicted_efficiency
            ) /
            predicted_efficiency
        ) * 100

        now = LearningService.utcnow()

        observation = TripObservation(
            id=str(uuid4()),
            vehicle_id=request.vehicle_id,
            trip_date=request.trip_date,
            origin=request.origin,
            destination=request.destination,
            distance_km=LearningService.round_value(
                request.distance_km,
                3
            ),
            starting_soc=LearningService.round_value(
                request.starting_soc,
                2
            ),
            ending_soc=LearningService.round_value(
                request.ending_soc,
                2
            ),
            charged_energy_kwh=LearningService.round_value(
                request.charged_energy_kwh or 0.0,
                3
            ),
            predicted_efficiency_kwh_per_100km=LearningService.round_value(
                predicted_efficiency,
                3
            ),
            predicted_energy_used_kwh=LearningService.round_value(
                predicted_energy_used_kwh,
                3
            ),
            actual_energy_used_kwh=LearningService.round_value(
                actual_energy_used_kwh,
                3
            ),
            actual_efficiency_kwh_per_100km=LearningService.round_value(
                actual_efficiency,
                3
            ),
            prediction_error_percent=LearningService.round_value(
                prediction_error_percent,
                3
            ),
            correction_factor=LearningService.round_value(
                correction_factor,
                5
            ),
            outside_temperature_c=request.outside_temperature_c,
            average_speed_kmh=request.average_speed_kmh,
            highway_ratio=request.highway_ratio,
            climate_control=request.climate_control,
            tire_pressure_note=request.tire_pressure_note,
            payload_note=request.payload_note,
            notes=request.notes,
            created_at=now
        )

        LearningRepository.save_observation(
            observation.to_dict()
        )

        profile = LearningService.recalculate_profile(
            vehicle_id=request.vehicle_id
        )

        return {
            "observation": observation.to_dict(),
            "profile": profile
        }

    @staticmethod
    def get_profile(vehicle_id):
        profile = LearningRepository.get_profile(
            vehicle_id
        )

        if profile is not None:
            return profile

        return LearningService.empty_profile(
            vehicle_id=vehicle_id
        )

    @staticmethod
    def list_observations(vehicle_id):
        observations = LearningRepository.list_observations(
            vehicle_id=vehicle_id
        )

        return {
            "vehicle_id": vehicle_id,
            "observations": observations
        }

    @staticmethod
    def recalculate_profile(vehicle_id):
        observations = LearningRepository.list_observations(
            vehicle_id=vehicle_id
        )

        if not observations:
            profile = LearningService.empty_profile(
                vehicle_id=vehicle_id
            )

            LearningRepository.save_profile(
                profile
            )

            return profile

        total_distance_km = sum(
            observation["distance_km"]
            for observation in observations
        )

        total_actual_energy_kwh = sum(
            observation["actual_energy_used_kwh"]
            for observation in observations
        )

        total_predicted_energy_kwh = sum(
            observation["predicted_energy_used_kwh"]
            for observation in observations
        )

        average_actual_efficiency = (
            total_actual_energy_kwh /
            total_distance_km
        ) * 100

        average_predicted_efficiency = (
            total_predicted_energy_kwh /
            total_distance_km
        ) * 100

        correction_factor = (
            average_actual_efficiency /
            average_predicted_efficiency
        )

        average_prediction_error_percent = (
            (
                average_actual_efficiency -
                average_predicted_efficiency
            ) /
            average_predicted_efficiency
        ) * 100

        confidence_score = LearningService.confidence_score(
            observation_count=len(observations),
            total_distance_km=total_distance_km
        )

        last_observation = observations[-1]

        profile = LearningProfile(
            vehicle_id=vehicle_id,
            observation_count=len(observations),
            total_distance_km=LearningService.round_value(
                total_distance_km,
                3
            ),
            average_predicted_efficiency_kwh_per_100km=LearningService.round_value(
                average_predicted_efficiency,
                3
            ),
            average_actual_efficiency_kwh_per_100km=LearningService.round_value(
                average_actual_efficiency,
                3
            ),
            correction_factor=LearningService.round_value(
                correction_factor,
                5
            ),
            average_prediction_error_percent=LearningService.round_value(
                average_prediction_error_percent,
                3
            ),
            confidence_score=confidence_score,
            last_observation_id=last_observation["id"],
            updated_at=LearningService.utcnow()
        )

        LearningRepository.save_profile(
            profile.to_dict()
        )

        return profile.to_dict()

    @staticmethod
    def calculate_actual_energy_used(request, vehicle):
        if request.actual_energy_used_kwh is not None:
            if request.actual_energy_used_kwh <= 0:
                raise ValueError(
                    "actual_energy_used_kwh must be greater than 0"
                )

            return request.actual_energy_used_kwh

        usable_battery_kwh = vehicle.usable_battery_kwh

        starting_energy_kwh = (
            usable_battery_kwh *
            request.starting_soc /
            100
        )

        ending_energy_kwh = (
            usable_battery_kwh *
            request.ending_soc /
            100
        )

        charged_energy_kwh = (
            request.charged_energy_kwh or 0.0
        )

        actual_energy_used_kwh = (
            starting_energy_kwh +
            charged_energy_kwh -
            ending_energy_kwh
        )

        if actual_energy_used_kwh <= 0:
            raise ValueError(
                "Unable to calculate actual energy used. "
                "Provide actual_energy_used_kwh or valid SOC and charged_energy_kwh values."
            )

        return actual_energy_used_kwh

    @staticmethod
    def calculate_predicted_energy_used(request):
        if request.predicted_energy_used_kwh is not None:
            return request.predicted_energy_used_kwh

        return (
            request.distance_km *
            request.predicted_efficiency_kwh_per_100km /
            100
        )

    @staticmethod
    def get_vehicle(vehicle_id):
        try:
            vehicle = VehicleRegistry.get(
                vehicle_id
            )

            if vehicle is None:
                raise ValueError()

            return vehicle

        except Exception as error:
            raise ValueError(
                f"Unknown vehicle_id: {vehicle_id}"
            ) from error

    @staticmethod
    def empty_profile(vehicle_id):
        return {
            "vehicle_id": vehicle_id,
            "observation_count": 0,
            "total_distance_km": 0.0,
            "average_predicted_efficiency_kwh_per_100km": 0.0,
            "average_actual_efficiency_kwh_per_100km": 0.0,
            "correction_factor": 1.0,
            "average_prediction_error_percent": 0.0,
            "confidence_score": 0.0,
            "last_observation_id": None,
            "updated_at": None
        }

    @staticmethod
    def confidence_score(
        observation_count,
        total_distance_km
    ):
        count_score = min(
            observation_count / 10,
            1.0
        )

        distance_score = min(
            total_distance_km / 2000,
            1.0
        )

        score = (
            count_score * 0.6 +
            distance_score * 0.4
        )

        return LearningService.round_value(
            score,
            3
        )

    @staticmethod
    def utcnow():
        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def round_value(value, digits):
        return round(
            float(value),
            digits
        )