from dataclasses import dataclass
from typing import Any


@dataclass
class TripConditionsImpact:
    applied: bool

    efficiency_adjustment_kwh_per_100km: float
    energy_impact_kwh: float
    soc_impact_percent: float | None

    passenger_cargo_impact_kwh: float
    climate_impact_kwh: float
    driving_style_impact_kwh: float
    road_condition_impact_kwh: float
    tire_impact_kwh: float
    roof_load_impact_kwh: float

    battery_degradation_percent: float | None
    effective_usable_battery_kwh: float | None
    usable_battery_reduction_kwh: float | None

    factors: list[str]
    warnings: list[str]


class TripConditionsService:
    PASSENGER_WEIGHT_KG = 75.0
    BASE_INCLUDED_PASSENGERS = 1

    KG_WEIGHT_IMPACT_KWH_PER_100KM = 0.0035

    CLIMATE_ADJUSTMENTS = {
        "off": 0.0,
        "eco": 0.5,
        "normal": 1.2,
        "high": 2.5
    }

    DRIVING_STYLE_ADJUSTMENTS = {
        "eco": -1.0,
        "normal": 0.0,
        "sport": 1.8,
        "aggressive": 3.5
    }

    ROAD_CONDITION_ADJUSTMENTS = {
        "dry": 0.0,
        "wet": 1.0,
        "snow": 3.5,
        "ice": 4.5
    }

    TIRE_CONDITION_ADJUSTMENTS = {
        "normal": 0.0,
        "low_pressure": 2.0,
        "winter_tires": 1.0
    }

    ROOF_LOAD_ADJUSTMENTS = {
        "none": 0.0,
        "roof_rack": 1.2,
        "cargo_box": 3.0
    }

    MAX_BATTERY_DEGRADATION_PERCENT = 40.0

    @staticmethod
    def build(
        conditions: Any,
        distance_km: float | None,
        usable_battery_kwh: float | None
    ) -> TripConditionsImpact:
        normalized = TripConditionsService.normalize_conditions(
            conditions
        )

        distance_km = TripConditionsService.safe_float(
            distance_km,
            0.0
        )

        usable_battery_kwh = TripConditionsService.safe_float(
            usable_battery_kwh,
            0.0
        )

        factors = []
        warnings = []

        passenger_cargo_adjustment = (
            TripConditionsService.passenger_cargo_adjustment(
                normalized=normalized,
                factors=factors
            )
        )

        climate_adjustment = TripConditionsService.climate_adjustment(
            normalized=normalized,
            factors=factors
        )

        driving_style_adjustment = TripConditionsService.table_adjustment(
            normalized=normalized,
            field_name="driving_style",
            table=TripConditionsService.DRIVING_STYLE_ADJUSTMENTS,
            factor_prefix="Driving style",
            factors=factors
        )

        road_condition_adjustment = TripConditionsService.table_adjustment(
            normalized=normalized,
            field_name="road_condition",
            table=TripConditionsService.ROAD_CONDITION_ADJUSTMENTS,
            factor_prefix="Road condition",
            factors=factors
        )

        tire_adjustment = TripConditionsService.table_adjustment(
            normalized=normalized,
            field_name="tire_condition",
            table=TripConditionsService.TIRE_CONDITION_ADJUSTMENTS,
            factor_prefix="Tire condition",
            factors=factors
        )

        roof_adjustment = TripConditionsService.table_adjustment(
            normalized=normalized,
            field_name="roof_load",
            table=TripConditionsService.ROOF_LOAD_ADJUSTMENTS,
            factor_prefix="Roof load",
            factors=factors
        )

        total_adjustment = (
            passenger_cargo_adjustment +
            climate_adjustment +
            driving_style_adjustment +
            road_condition_adjustment +
            tire_adjustment +
            roof_adjustment
        )

        energy_impact = TripConditionsService.energy_from_adjustment(
            distance_km=distance_km,
            adjustment_kwh_per_100km=total_adjustment
        )

        soc_impact = TripConditionsService.soc_impact(
            energy_kwh=energy_impact,
            usable_battery_kwh=usable_battery_kwh
        )

        degradation = TripConditionsService.battery_degradation_percent(
            normalized=normalized,
            factors=factors,
            warnings=warnings
        )

        effective_usable_battery = None
        usable_battery_reduction = None

        if degradation is not None and usable_battery_kwh > 0:
            effective_usable_battery = (
                usable_battery_kwh *
                (1 - (degradation / 100))
            )

            usable_battery_reduction = (
                usable_battery_kwh -
                effective_usable_battery
            )

        applied = (
            total_adjustment != 0 or
            degradation is not None
        )

        return TripConditionsImpact(
            applied=applied,
            efficiency_adjustment_kwh_per_100km=TripConditionsService.round_value(
                total_adjustment
            ),
            energy_impact_kwh=TripConditionsService.round_value(
                energy_impact
            ),
            soc_impact_percent=TripConditionsService.round_optional(
                soc_impact
            ),
            passenger_cargo_impact_kwh=TripConditionsService.round_value(
                TripConditionsService.energy_from_adjustment(
                    distance_km=distance_km,
                    adjustment_kwh_per_100km=passenger_cargo_adjustment
                )
            ),
            climate_impact_kwh=TripConditionsService.round_value(
                TripConditionsService.energy_from_adjustment(
                    distance_km=distance_km,
                    adjustment_kwh_per_100km=climate_adjustment
                )
            ),
            driving_style_impact_kwh=TripConditionsService.round_value(
                TripConditionsService.energy_from_adjustment(
                    distance_km=distance_km,
                    adjustment_kwh_per_100km=driving_style_adjustment
                )
            ),
            road_condition_impact_kwh=TripConditionsService.round_value(
                TripConditionsService.energy_from_adjustment(
                    distance_km=distance_km,
                    adjustment_kwh_per_100km=road_condition_adjustment
                )
            ),
            tire_impact_kwh=TripConditionsService.round_value(
                TripConditionsService.energy_from_adjustment(
                    distance_km=distance_km,
                    adjustment_kwh_per_100km=tire_adjustment
                )
            ),
            roof_load_impact_kwh=TripConditionsService.round_value(
                TripConditionsService.energy_from_adjustment(
                    distance_km=distance_km,
                    adjustment_kwh_per_100km=roof_adjustment
                )
            ),
            battery_degradation_percent=degradation,
            effective_usable_battery_kwh=TripConditionsService.round_optional(
                effective_usable_battery
            ),
            usable_battery_reduction_kwh=TripConditionsService.round_optional(
                usable_battery_reduction
            ),
            factors=TripConditionsService.unique_list(
                factors
            ),
            warnings=TripConditionsService.unique_list(
                warnings
            )
        )

    @staticmethod
    def normalize_conditions(conditions: Any) -> dict:
        if conditions is None:
            return {}

        if isinstance(conditions, dict):
            return {
                key: value
                for key, value in conditions.items()
                if value is not None and value != ""
            }

        normalized = {}

        for name in [
            "passengers",
            "cargo_weight_kg",
            "climate_control",
            "cabin_target_temp_c",
            "driving_style",
            "road_condition",
            "tire_condition",
            "roof_load",
            "battery_degradation_percent"
        ]:
            value = getattr(
                conditions,
                name,
                None
            )

            if value is not None and value != "":
                normalized[name] = value

        return normalized

    @staticmethod
    def passenger_cargo_adjustment(
        normalized,
        factors
    ):
        passengers = normalized.get(
            "passengers"
        )

        cargo_weight_kg = normalized.get(
            "cargo_weight_kg"
        )

        passengers = TripConditionsService.safe_float(
            passengers,
            None
        )

        cargo_weight_kg = TripConditionsService.safe_float(
            cargo_weight_kg,
            None
        )

        extra_weight_kg = 0.0

        if passengers is not None:
            extra_passengers = max(
                passengers - TripConditionsService.BASE_INCLUDED_PASSENGERS,
                0.0
            )

            extra_weight_kg += (
                extra_passengers *
                TripConditionsService.PASSENGER_WEIGHT_KG
            )

            factors.append(
                f"Passengers: {int(passengers)}"
            )

        if cargo_weight_kg is not None:
            extra_weight_kg += max(
                cargo_weight_kg,
                0.0
            )

            factors.append(
                f"Cargo: {round(cargo_weight_kg, 1)} kg"
            )

        return (
            extra_weight_kg *
            TripConditionsService.KG_WEIGHT_IMPACT_KWH_PER_100KM
        )

    @staticmethod
    def climate_adjustment(
        normalized,
        factors
    ):
        climate_control = normalized.get(
            "climate_control"
        )

        adjustment = 0.0

        if climate_control:
            value = str(
                climate_control
            ).lower()

            adjustment += TripConditionsService.CLIMATE_ADJUSTMENTS.get(
                value,
                0.0
            )

            factors.append(
                f"Climate: {value}"
            )

        cabin_target = TripConditionsService.safe_float(
            normalized.get(
                "cabin_target_temp_c"
            ),
            None
        )

        if cabin_target is not None:
            if cabin_target <= 18:
                adjustment += 0.4
                factors.append(
                    f"Cool cabin target: {cabin_target:.1f} C"
                )

            elif cabin_target >= 25:
                adjustment += 0.4
                factors.append(
                    f"Warm cabin target: {cabin_target:.1f} C"
                )

        return adjustment

    @staticmethod
    def table_adjustment(
        normalized,
        field_name,
        table,
        factor_prefix,
        factors
    ):
        value = normalized.get(
            field_name
        )

        if not value:
            return 0.0

        normalized_value = str(
            value
        ).lower()

        if normalized_value not in table:
            return 0.0

        factors.append(
            f"{factor_prefix}: {normalized_value}"
        )

        return table[normalized_value]

    @staticmethod
    def battery_degradation_percent(
        normalized,
        factors,
        warnings
    ):
        value = TripConditionsService.safe_float(
            normalized.get(
                "battery_degradation_percent"
            ),
            None
        )

        if value is None:
            return None

        value = max(
            0.0,
            min(
                value,
                TripConditionsService.MAX_BATTERY_DEGRADATION_PERCENT
            )
        )

        if value > 0:
            factors.append(
                f"Battery degradation: {value:.1f}%"
            )

        if value >= 15:
            warnings.append(
                "Battery degradation is high enough to noticeably reduce usable range."
            )

        return value

    @staticmethod
    def energy_from_adjustment(
        distance_km,
        adjustment_kwh_per_100km
    ):
        return (
            distance_km *
            adjustment_kwh_per_100km /
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

        return (
            energy_kwh /
            usable_battery_kwh
        ) * 100

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
        digits=2
    ):
        return round(
            value,
            digits
        )

    @staticmethod
    def round_optional(
        value,
        digits=2
    ):
        if value is None:
            return None

        return round(
            value,
            digits
        )