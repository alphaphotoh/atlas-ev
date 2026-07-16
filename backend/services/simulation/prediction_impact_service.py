from dataclasses import dataclass
from typing import Any

from backend.services.simulation.efficiency_profile_service import (
    EfficiencyProfileService,
)

from backend.services.simulation.heading_service import (
    HeadingService,
)

from backend.services.simulation.elevation_impact_service import (
    ElevationImpactService,
)


@dataclass
class PredictionImpactBreakdown:
    vehicle_base_energy_kwh: float
    learned_base_energy_kwh: float
    final_energy_kwh: float

    learning_impact_kwh: float
    temperature_impact_kwh: float
    wind_impact_kwh: float
    elevation_impact_kwh: float
    conditions_impact_kwh: float
    total_impact_kwh: float

    learning_soc_impact_percent: float | None
    temperature_soc_impact_percent: float | None
    wind_soc_impact_percent: float | None
    elevation_soc_impact_percent: float | None
    conditions_soc_impact_percent: float | None
    total_soc_impact_percent: float | None

    elevation_gain_m: float
    elevation_loss_m: float
    net_elevation_change_m: float

    warnings: list[str]


class PredictionImpactService:

    @staticmethod
    def build(
        route,
        environment_samples: list[Any],
        vehicle_base_efficiency: float | None,
        learned_efficiency: float | None,
        final_energy_kwh: float | None,
        usable_battery_kwh: float | None
    ) -> PredictionImpactBreakdown:
        distance_km = PredictionImpactService.safe_float(
            getattr(
                route,
                "distance_km",
                0.0
            ),
            0.0
        )

        vehicle_base_efficiency = PredictionImpactService.safe_float(
            vehicle_base_efficiency,
            0.0
        )

        learned_efficiency = PredictionImpactService.safe_float(
            learned_efficiency,
            vehicle_base_efficiency
        )

        vehicle_base_energy = PredictionImpactService.energy_from_efficiency(
            distance_km=distance_km,
            efficiency=vehicle_base_efficiency
        )

        learned_base_energy = PredictionImpactService.energy_from_efficiency(
            distance_km=distance_km,
            efficiency=learned_efficiency
        )

        learning_impact = (
            learned_base_energy -
            vehicle_base_energy
        )

        condition_impacts = PredictionImpactService.calculate_condition_impacts(
            route=route,
            environment_samples=environment_samples,
            distance_km=distance_km
        )

        calculated_final_energy = (
            learned_base_energy +
            condition_impacts["temperature_impact_kwh"] +
            condition_impacts["wind_impact_kwh"] +
            condition_impacts["elevation_impact_kwh"]
        )

        if final_energy_kwh is None:
            final_energy = calculated_final_energy
        else:
            final_energy = PredictionImpactService.safe_float(
                final_energy_kwh,
                calculated_final_energy
            )

        conditions_impact = (
            final_energy -
            learned_base_energy
        )

        total_impact = (
            final_energy -
            vehicle_base_energy
        )

        elevation = ElevationImpactService.analyze_samples(
            samples=environment_samples,
            distance_km=distance_km,
            usable_battery_kwh=usable_battery_kwh
        )

        warnings = []

        warnings.extend(
            condition_impacts["warnings"]
        )

        warnings.extend(
            elevation.warnings
        )

        return PredictionImpactBreakdown(
            vehicle_base_energy_kwh=PredictionImpactService.round_value(
                vehicle_base_energy
            ),
            learned_base_energy_kwh=PredictionImpactService.round_value(
                learned_base_energy
            ),
            final_energy_kwh=PredictionImpactService.round_value(
                final_energy
            ),
            learning_impact_kwh=PredictionImpactService.round_value(
                learning_impact
            ),
            temperature_impact_kwh=PredictionImpactService.round_value(
                condition_impacts["temperature_impact_kwh"]
            ),
            wind_impact_kwh=PredictionImpactService.round_value(
                condition_impacts["wind_impact_kwh"]
            ),
            elevation_impact_kwh=PredictionImpactService.round_value(
                condition_impacts["elevation_impact_kwh"]
            ),
            conditions_impact_kwh=PredictionImpactService.round_value(
                conditions_impact
            ),
            total_impact_kwh=PredictionImpactService.round_value(
                total_impact
            ),
            learning_soc_impact_percent=PredictionImpactService.soc_impact(
                energy_kwh=learning_impact,
                usable_battery_kwh=usable_battery_kwh
            ),
            temperature_soc_impact_percent=PredictionImpactService.soc_impact(
                energy_kwh=condition_impacts["temperature_impact_kwh"],
                usable_battery_kwh=usable_battery_kwh
            ),
            wind_soc_impact_percent=PredictionImpactService.soc_impact(
                energy_kwh=condition_impacts["wind_impact_kwh"],
                usable_battery_kwh=usable_battery_kwh
            ),
            elevation_soc_impact_percent=PredictionImpactService.soc_impact(
                energy_kwh=condition_impacts["elevation_impact_kwh"],
                usable_battery_kwh=usable_battery_kwh
            ),
            conditions_soc_impact_percent=PredictionImpactService.soc_impact(
                energy_kwh=conditions_impact,
                usable_battery_kwh=usable_battery_kwh
            ),
            total_soc_impact_percent=PredictionImpactService.soc_impact(
                energy_kwh=total_impact,
                usable_battery_kwh=usable_battery_kwh
            ),
            elevation_gain_m=elevation.elevation_gain_m,
            elevation_loss_m=elevation.elevation_loss_m,
            net_elevation_change_m=elevation.net_elevation_change_m,
            warnings=warnings
        )

    @staticmethod
    def calculate_condition_impacts(
        route,
        environment_samples,
        distance_km
    ):
        clean_samples = PredictionImpactService.clean_samples(
            environment_samples
        )

        if not clean_samples:
            return {
                "temperature_impact_kwh": 0.0,
                "wind_impact_kwh": 0.0,
                "elevation_impact_kwh": 0.0,
                "warnings": [
                    "No route condition samples were available for prediction impact breakdown."
                ]
            }

        temperature_impact = 0.0
        wind_impact = 0.0
        elevation_impact = 0.0

        previous_distance = 0.0

        for sample in clean_samples:
            sample_distance = min(
                sample["distance_km"],
                distance_km
            )

            segment_distance = max(
                sample_distance - previous_distance,
                0.0
            )

            impacts = PredictionImpactService.sample_impacts(
                route=route,
                sample=sample,
                segment_distance_km=segment_distance
            )

            temperature_impact += impacts["temperature_impact_kwh"]
            wind_impact += impacts["wind_impact_kwh"]
            elevation_impact += impacts["elevation_impact_kwh"]

            previous_distance = sample_distance

        if previous_distance < distance_km:
            last_sample = clean_samples[-1]

            impacts = PredictionImpactService.sample_impacts(
                route=route,
                sample=last_sample,
                segment_distance_km=distance_km - previous_distance
            )

            temperature_impact += impacts["temperature_impact_kwh"]
            wind_impact += impacts["wind_impact_kwh"]
            elevation_impact += impacts["elevation_impact_kwh"]

        return {
            "temperature_impact_kwh": temperature_impact,
            "wind_impact_kwh": wind_impact,
            "elevation_impact_kwh": elevation_impact,
            "warnings": []
        }

    @staticmethod
    def sample_impacts(
        route,
        sample,
        segment_distance_km
    ):
        temperature_adjustment = (
            EfficiencyProfileService.temperature_adjustment(
                sample["temperature_c"]
            )
        )

        wind_adjustment = PredictionImpactService.wind_adjustment(
            route=route,
            sample=sample
        )

        elevation_adjustment = 0.0

        if sample["elevation_m"] is not None:
            elevation_adjustment = (
                EfficiencyProfileService.grade_adjustment(
                    sample["grade_percent"]
                )
            )

        return {
            "temperature_impact_kwh": (
                segment_distance_km *
                temperature_adjustment /
                100
            ),
            "wind_impact_kwh": (
                segment_distance_km *
                wind_adjustment /
                100
            ),
            "elevation_impact_kwh": (
                segment_distance_km *
                elevation_adjustment /
                100
            )
        }

    @staticmethod
    def wind_adjustment(
        route,
        sample
    ):
        wind_speed = sample["wind_speed_kph"]

        if not wind_speed:
            return 0.0

        wind_direction = sample["wind_direction_degrees"]

        if wind_direction is None:
            return 0.0

        try:
            heading = HeadingService.heading_at_distance(
                route,
                sample["distance_km"]
            )
        except Exception:
            heading = 0.0

        return EfficiencyProfileService.wind_adjustment(
            wind_speed_kph=wind_speed,
            wind_direction_degrees=wind_direction,
            vehicle_heading=heading
        )

    @staticmethod
    def clean_samples(
        environment_samples
    ):
        clean = []

        for sample in environment_samples or []:
            weather = PredictionImpactService.get_value(
                sample,
                "weather"
            )

            if weather is None:
                continue

            distance_km = PredictionImpactService.safe_float(
                PredictionImpactService.get_value(
                    sample,
                    "route_distance_km"
                ),
                0.0
            )

            clean.append(
                {
                    "distance_km": distance_km,
                    "temperature_c": PredictionImpactService.safe_float(
                        PredictionImpactService.get_value(
                            weather,
                            "temperature_c"
                        ),
                        20.0
                    ),
                    "wind_speed_kph": PredictionImpactService.safe_float(
                        PredictionImpactService.get_value(
                            weather,
                            "wind_speed_kph"
                        ),
                        0.0
                    ),
                    "wind_direction_degrees": PredictionImpactService.get_value(
                        weather,
                        "wind_direction_degrees"
                    ),
                    "elevation_m": PredictionImpactService.get_value(
                        sample,
                        "elevation_m"
                    ),
                    "grade_percent": PredictionImpactService.safe_float(
                        PredictionImpactService.get_value(
                            sample,
                            "grade_percent"
                        ),
                        0.0
                    )
                }
            )

        clean.sort(
            key=lambda item: item["distance_km"]
        )

        return clean

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
    def energy_from_efficiency(
        distance_km,
        efficiency
    ):
        return (
            distance_km *
            efficiency /
            100
        )

    @staticmethod
    def soc_impact(
        energy_kwh,
        usable_battery_kwh
    ):
        if not usable_battery_kwh:
            return None

        if usable_battery_kwh <= 0:
            return None

        return PredictionImpactService.round_value(
            (
                energy_kwh /
                usable_battery_kwh
            ) * 100
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
    def round_value(
        value,
        digits=2
    ):
        return round(
            value,
            digits
        )