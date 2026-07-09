import csv
import io

from datetime import datetime, timezone
from uuid import uuid4

from backend.models.learning_profile import LearningProfile
from backend.models.registry import VehicleRegistry
from backend.models.trip_observation import TripObservation
from backend.schemas.learning import TripObservationUploadRequest
from backend.services.learning.learning_repository import LearningRepository


class LearningService:
    EMPTY_VALUES = {
        "",
        "none",
        "null",
        "n/a",
        "na"
    }

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
    def import_csv_text(
        csv_text,
        default_vehicle_id=None
    ):
        if csv_text is None:
            raise ValueError(
                "CSV content is required"
            )

        csv_text = csv_text.strip()

        if not csv_text:
            raise ValueError(
                "CSV content is empty"
            )

        reader = csv.DictReader(
            io.StringIO(csv_text)
        )

        if not reader.fieldnames:
            raise ValueError(
                "CSV header row is missing"
            )

        observations = []
        errors = []
        vehicle_ids = set()
        last_profile = None

        for row_number, row in enumerate(
            reader,
            start=2
        ):
            try:
                request = LearningService.build_upload_request_from_csv_row(
                    row=row,
                    default_vehicle_id=default_vehicle_id
                )

                response = LearningService.upload_trip(
                    request
                )

                observations.append(
                    response["observation"]
                )

                last_profile = response["profile"]

                vehicle_ids.add(
                    request.vehicle_id
                )

            except Exception as error:
                errors.append(
                    {
                        "row_number": row_number,
                        "error": str(error),
                        "data": LearningService.clean_csv_error_data(
                            row
                        )
                    }
                )

        vehicle_id = None

        if len(vehicle_ids) == 1:
            vehicle_id = next(
                iter(vehicle_ids)
            )

        return {
            "vehicle_id": vehicle_id,
            "imported_count": len(observations),
            "failed_count": len(errors),
            "observations": observations,
            "profile": last_profile,
            "errors": errors
        }

    @staticmethod
    def build_upload_request_from_csv_row(
        row,
        default_vehicle_id=None
    ):
        normalized_row = LearningService.normalize_csv_row(
            row
        )

        vehicle_id = LearningService.get_csv_string(
            normalized_row,
            [
                "vehicle_id",
                "vehicle",
                "car"
            ],
            default_value=default_vehicle_id
        )

        if not vehicle_id:
            raise ValueError(
                "vehicle_id is required"
            )

        return TripObservationUploadRequest(
            vehicle_id=vehicle_id,
            trip_date=LearningService.get_csv_string(
                normalized_row,
                [
                    "trip_date",
                    "date"
                ]
            ),
            origin=LearningService.get_csv_string(
                normalized_row,
                [
                    "origin",
                    "start",
                    "from"
                ]
            ),
            destination=LearningService.get_csv_string(
                normalized_row,
                [
                    "destination",
                    "end",
                    "to"
                ]
            ),
            distance_km=LearningService.get_required_csv_float(
                normalized_row,
                [
                    "distance_km",
                    "distance"
                ]
            ),
            starting_soc=LearningService.get_required_csv_float(
                normalized_row,
                [
                    "starting_soc",
                    "start_soc",
                    "starting_soc_percent"
                ]
            ),
            ending_soc=LearningService.get_required_csv_float(
                normalized_row,
                [
                    "ending_soc",
                    "end_soc",
                    "ending_soc_percent"
                ]
            ),
            charged_energy_kwh=LearningService.get_optional_csv_float(
                normalized_row,
                [
                    "charged_energy_kwh",
                    "charging_energy_kwh",
                    "charge_added_kwh"
                ],
                default_value=0.0
            ),
            actual_energy_used_kwh=LearningService.get_optional_csv_float(
                normalized_row,
                [
                    "actual_energy_used_kwh",
                    "actual_energy_kwh",
                    "energy_used_kwh"
                ]
            ),
            predicted_efficiency_kwh_per_100km=LearningService.get_required_csv_float(
                normalized_row,
                [
                    "predicted_efficiency_kwh_per_100km",
                    "predicted_efficiency",
                    "planner_efficiency"
                ]
            ),
            predicted_energy_used_kwh=LearningService.get_optional_csv_float(
                normalized_row,
                [
                    "predicted_energy_used_kwh",
                    "predicted_energy_kwh",
                    "planner_energy_kwh"
                ]
            ),
            outside_temperature_c=LearningService.get_optional_csv_float(
                normalized_row,
                [
                    "outside_temperature_c",
                    "temperature_c",
                    "temp_c"
                ]
            ),
            average_speed_kmh=LearningService.get_optional_csv_float(
                normalized_row,
                [
                    "average_speed_kmh",
                    "avg_speed_kmh",
                    "average_speed"
                ]
            ),
            highway_ratio=LearningService.get_optional_csv_float(
                normalized_row,
                [
                    "highway_ratio",
                    "highway_percent"
                ]
            ),
            climate_control=LearningService.get_csv_string(
                normalized_row,
                [
                    "climate_control",
                    "hvac",
                    "ac_heater"
                ]
            ),
            tire_pressure_note=LearningService.get_csv_string(
                normalized_row,
                [
                    "tire_pressure_note",
                    "tire_pressure"
                ]
            ),
            payload_note=LearningService.get_csv_string(
                normalized_row,
                [
                    "payload_note",
                    "payload",
                    "passengers"
                ]
            ),
            notes=LearningService.get_csv_string(
                normalized_row,
                [
                    "notes",
                    "note"
                ]
            )
        )

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
    def normalize_csv_row(row):
        normalized = {}

        for key, value in row.items():
            if key is None:
                continue

            normalized_key = (
                key.strip()
                .lower()
                .replace(" ", "_")
                .replace("-", "_")
            )

            normalized[
                normalized_key
            ] = value

        return normalized

    @staticmethod
    def get_csv_string(
        row,
        names,
        default_value=None
    ):
        for name in names:
            value = row.get(
                name
            )

            if not LearningService.is_empty_value(
                value
            ):
                return str(
                    value
                ).strip()

        return default_value

    @staticmethod
    def get_required_csv_float(
        row,
        names
    ):
        value = LearningService.get_optional_csv_float(
            row=row,
            names=names
        )

        if value is None:
            raise ValueError(
                f"Missing required numeric column: {names[0]}"
            )

        return value

    @staticmethod
    def get_optional_csv_float(
        row,
        names,
        default_value=None
    ):
        for name in names:
            value = row.get(
                name
            )

            if LearningService.is_empty_value(
                value
            ):
                continue

            try:
                return float(
                    str(value).strip()
                )

            except ValueError as error:
                raise ValueError(
                    f"Invalid numeric value for {name}: {value}"
                ) from error

        return default_value

    @staticmethod
    def is_empty_value(value):
        if value is None:
            return True

        return (
            str(value).strip().lower()
            in LearningService.EMPTY_VALUES
        )

    @staticmethod
    def clean_csv_error_data(row):
        cleaned = {}

        for key, value in row.items():
            if key is None:
                continue

            cleaned[
                key
            ] = value

        return cleaned

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