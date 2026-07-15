from dataclasses import dataclass
from typing import Any


@dataclass
class SocUncertainty:
    arrival_soc_most_likely_percent: float
    arrival_soc_low_percent: float
    arrival_soc_high_percent: float

    confidence_score: float

    energy_uncertainty_kwh: float
    soc_uncertainty_percent: float
    uncertainty_percent: float

    factors: list[str]
    warnings: list[str]


class UncertaintyService:
    MIN_CONFIDENCE = 0.55
    MAX_CONFIDENCE = 0.95

    BASE_UNCERTAINTY_PERCENT = 0.04
    NO_ROUTE_CONDITIONS_PERCENT = 0.06
    NO_LEARNING_PERCENT = 0.03
    COLD_WEATHER_PERCENT = 0.04
    HOT_WEATHER_PERCENT = 0.02
    HIGH_WIND_PERCENT = 0.03
    HIGH_ELEVATION_PERCENT = 0.03
    LONG_TRIP_PERCENT = 0.02

    @staticmethod
    def build(
        estimated_arrival_soc_percent: float,
        usable_battery_kwh: float | None,
        energy_used_kwh: float | None,
        distance_km: float | None,
        environment_samples: list[Any] | None,
        learning_confidence_score: float | None = None
    ) -> SocUncertainty:
        usable_battery_kwh = UncertaintyService.safe_float(
            usable_battery_kwh,
            0.0
        )

        energy_used_kwh = UncertaintyService.safe_float(
            energy_used_kwh,
            0.0
        )

        distance_km = UncertaintyService.safe_float(
            distance_km,
            0.0
        )

        estimated_arrival_soc_percent = UncertaintyService.safe_float(
            estimated_arrival_soc_percent,
            0.0
        )

        learning_confidence_score = UncertaintyService.safe_float(
            learning_confidence_score,
            0.0
        )

        samples = UncertaintyService.clean_samples(
            environment_samples or []
        )

        factors = []
        warnings = []

        uncertainty_percent = UncertaintyService.BASE_UNCERTAINTY_PERCENT

        factors.append(
            "Base model uncertainty"
        )

        if not samples:
            uncertainty_percent += UncertaintyService.NO_ROUTE_CONDITIONS_PERCENT
            factors.append(
                "No route weather/elevation samples"
            )
            warnings.append(
                "SOC range is wider because route condition samples were not available."
            )
        else:
            condition_result = UncertaintyService.condition_uncertainty(
                samples=samples
            )

            uncertainty_percent += condition_result["uncertainty_percent"]
            factors.extend(
                condition_result["factors"]
            )
            warnings.extend(
                condition_result["warnings"]
            )

        if learning_confidence_score <= 0:
            uncertainty_percent += UncertaintyService.NO_LEARNING_PERCENT
            factors.append(
                "Limited learning history"
            )

        elif learning_confidence_score < 0.6:
            learning_penalty = (
                UncertaintyService.NO_LEARNING_PERCENT *
                (1 - learning_confidence_score)
            )

            uncertainty_percent += learning_penalty
            factors.append(
                "Moderate learning confidence"
            )

        else:
            factors.append(
                "Learning profile available"
            )

        if distance_km >= 400:
            uncertainty_percent += UncertaintyService.LONG_TRIP_PERCENT
            factors.append(
                "Long trip distance"
            )

        energy_uncertainty_kwh = (
            energy_used_kwh *
            uncertainty_percent
        )

        soc_uncertainty_percent = 0.0

        if usable_battery_kwh > 0:
            soc_uncertainty_percent = (
                energy_uncertainty_kwh /
                usable_battery_kwh
            ) * 100

        arrival_soc_low = max(
            0.0,
            estimated_arrival_soc_percent - soc_uncertainty_percent
        )

        arrival_soc_high = min(
            100.0,
            estimated_arrival_soc_percent + soc_uncertainty_percent
        )

        confidence_score = UncertaintyService.confidence_from_uncertainty(
            uncertainty_percent=uncertainty_percent,
            learning_confidence_score=learning_confidence_score,
            has_samples=bool(samples)
        )

        if arrival_soc_low < 10:
            warnings.append(
                "Conservative SOC estimate is below the preferred 10% safety buffer."
            )

        return SocUncertainty(
            arrival_soc_most_likely_percent=UncertaintyService.round_value(
                estimated_arrival_soc_percent,
                1
            ),
            arrival_soc_low_percent=UncertaintyService.round_value(
                arrival_soc_low,
                1
            ),
            arrival_soc_high_percent=UncertaintyService.round_value(
                arrival_soc_high,
                1
            ),
            confidence_score=UncertaintyService.round_value(
                confidence_score,
                2
            ),
            energy_uncertainty_kwh=UncertaintyService.round_value(
                energy_uncertainty_kwh,
                1
            ),
            soc_uncertainty_percent=UncertaintyService.round_value(
                soc_uncertainty_percent,
                1
            ),
            uncertainty_percent=UncertaintyService.round_value(
                uncertainty_percent * 100,
                1
            ),
            factors=UncertaintyService.unique_list(
                factors
            ),
            warnings=UncertaintyService.unique_list(
                warnings
            )
        )

    @staticmethod
    def condition_uncertainty(samples):
        uncertainty_percent = 0.0
        factors = []
        warnings = []

        temperatures = [
            sample["temperature_c"]
            for sample in samples
            if sample["temperature_c"] is not None
        ]

        wind_speeds = [
            sample["wind_speed_kph"]
            for sample in samples
            if sample["wind_speed_kph"] is not None
        ]

        elevations = [
            sample["elevation_m"]
            for sample in samples
            if sample["elevation_m"] is not None
        ]

        grades = [
            abs(
                sample["grade_percent"]
            )
            for sample in samples
            if sample["grade_percent"] is not None
        ]

        if temperatures:
            coldest = min(
                temperatures
            )

            hottest = max(
                temperatures
            )

            if coldest <= 0:
                uncertainty_percent += UncertaintyService.COLD_WEATHER_PERCENT
                factors.append(
                    "Cold weather risk"
                )
                warnings.append(
                    "Cold weather can increase energy use and widen SOC uncertainty."
                )

            elif hottest >= 30:
                uncertainty_percent += UncertaintyService.HOT_WEATHER_PERCENT
                factors.append(
                    "Hot weather HVAC risk"
                )

            else:
                factors.append(
                    "Normal temperature range"
                )

        if wind_speeds:
            max_wind = max(
                wind_speeds
            )

            if max_wind >= 30:
                uncertainty_percent += UncertaintyService.HIGH_WIND_PERCENT
                factors.append(
                    "High wind risk"
                )
                warnings.append(
                    "High winds can materially affect highway range."
                )

            elif max_wind >= 15:
                uncertainty_percent += (
                    UncertaintyService.HIGH_WIND_PERCENT / 2
                )
                factors.append(
                    "Moderate wind risk"
                )

        if elevations:
            elevation_gain = UncertaintyService.elevation_gain(
                elevations
            )

            max_grade = 0.0

            if grades:
                max_grade = max(
                    grades
                )

            if elevation_gain >= 500 or max_grade >= 5:
                uncertainty_percent += UncertaintyService.HIGH_ELEVATION_PERCENT
                factors.append(
                    "Elevation/grade risk"
                )
                warnings.append(
                    "Elevation changes can widen the arrival SOC range."
                )

            elif elevation_gain > 0:
                factors.append(
                    "Elevation included"
                )

        return {
            "uncertainty_percent": uncertainty_percent,
            "factors": factors,
            "warnings": warnings
        }

    @staticmethod
    def elevation_gain(elevations):
        if len(elevations) < 2:
            return 0.0

        gain = 0.0
        previous = elevations[0]

        for elevation in elevations[1:]:
            difference = elevation - previous

            if difference > 0:
                gain += difference

            previous = elevation

        return gain

    @staticmethod
    def confidence_from_uncertainty(
        uncertainty_percent,
        learning_confidence_score,
        has_samples
    ):
        confidence = 1 - (
            uncertainty_percent * 3.8
        )

        if learning_confidence_score > 0:
            confidence += min(
                learning_confidence_score,
                1.0
            ) * 0.06

        if has_samples:
            confidence += 0.02

        confidence = max(
            UncertaintyService.MIN_CONFIDENCE,
            confidence
        )

        confidence = min(
            UncertaintyService.MAX_CONFIDENCE,
            confidence
        )

        return confidence

    @staticmethod
    def clean_samples(samples):
        clean = []

        for sample in samples:
            weather = UncertaintyService.get_value(
                sample,
                "weather"
            )

            clean.append(
                {
                    "temperature_c": UncertaintyService.get_nested_value(
                        weather,
                        "temperature_c"
                    ),
                    "wind_speed_kph": UncertaintyService.get_nested_value(
                        weather,
                        "wind_speed_kph"
                    ),
                    "elevation_m": UncertaintyService.get_value(
                        sample,
                        "elevation_m"
                    ),
                    "grade_percent": UncertaintyService.safe_float(
                        UncertaintyService.get_value(
                            sample,
                            "grade_percent"
                        ),
                        0.0
                    )
                }
            )

        return clean

    @staticmethod
    def get_nested_value(
        item,
        name
    ):
        if item is None:
            return None

        return UncertaintyService.get_value(
            item,
            name
        )

    @staticmethod
    def get_value(
        item,
        name
    ):
        if isinstance(item, dict):
            return item.get(
                name
            )

        return getattr(
            item,
            name,
            None
        )

    @staticmethod
    def safe_float(
        value,
        default_value
    ):
        if value is None:
            return default_value

        try:
            return float(
                value
            )

        except (TypeError, ValueError):
            return default_value

    @staticmethod
    def unique_list(values):
        unique = []

        for value in values:
            if value not in unique:
                unique.append(
                    value
                )

        return unique

    @staticmethod
    def round_value(
        value,
        digits
    ):
        return round(
            value,
            digits
        )