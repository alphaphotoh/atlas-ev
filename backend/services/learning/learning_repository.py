import json
import os
from pathlib import Path


class LearningRepository:
    DATA_DIR = Path(
        os.getenv(
            "ATLAS_EV_LEARNING_DIR",
            "data/learning"
        )
    )

    OBSERVATIONS_FILE = DATA_DIR / "trip_observations.json"
    PROFILES_FILE = DATA_DIR / "learning_profiles.json"

    @staticmethod
    def ensure_data_dir():
        LearningRepository.DATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

    @staticmethod
    def load_json(path, default_value):
        LearningRepository.ensure_data_dir()

        if not path.exists():
            return default_value

        try:
            content = path.read_text(
                encoding="utf-8"
            ).strip()

            if not content:
                return default_value

            return json.loads(content)

        except json.JSONDecodeError:
            return default_value

    @staticmethod
    def save_json(path, data):
        LearningRepository.ensure_data_dir()

        temp_path = path.with_suffix(
            path.suffix + ".tmp"
        )

        temp_path.write_text(
            json.dumps(
                data,
                indent=2
            ),
            encoding="utf-8"
        )

        temp_path.replace(path)

    @staticmethod
    def list_observations(vehicle_id=None):
        observations = LearningRepository.load_json(
            LearningRepository.OBSERVATIONS_FILE,
            []
        )

        if vehicle_id is None:
            return observations

        return [
            observation
            for observation in observations
            if observation.get("vehicle_id") == vehicle_id
        ]

    @staticmethod
    def save_observation(observation):
        observations = LearningRepository.list_observations()

        observations.append(
            observation
        )

        LearningRepository.save_json(
            LearningRepository.OBSERVATIONS_FILE,
            observations
        )

    @staticmethod
    def get_profile(vehicle_id):
        profiles = LearningRepository.load_json(
            LearningRepository.PROFILES_FILE,
            {}
        )

        return profiles.get(
            vehicle_id
        )

    @staticmethod
    def save_profile(profile):
        profiles = LearningRepository.load_json(
            LearningRepository.PROFILES_FILE,
            {}
        )

        profiles[
            profile["vehicle_id"]
        ] = profile

        LearningRepository.save_json(
            LearningRepository.PROFILES_FILE,
            profiles
        )