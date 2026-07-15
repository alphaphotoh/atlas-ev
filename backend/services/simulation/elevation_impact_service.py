from dataclasses import dataclass
from typing import Any


@dataclass
class ElevationImpact:
    elevation_gain_m: float
    elevation_loss_m: float
    net_elevation_change_m: float

    climb_energy_kwh: float
    regen_recovered_kwh: float
    net_energy_kwh: float

    soc_impact_percent: float | None
    efficiency_impact_kwh_per_100km: float | None

    warnings: list[str]


class ElevationImpactService:
    GRAVITY_M_PER_S2 = 9.80665
    JOULES_PER_KWH = 3_600_000

    DEFAULT_VEHICLE_MASS_KG = 2900.0
    DEFAULT_DRIVETRAIN_EFFICIENCY = 0.90
    DEFAULT_REGEN_EFFICIENCY = 0.60

    HIGH_ELEVATION_GAIN_WARNING_M = 500.0
    HIGH_SOC_IMPACT_WARNING_PERCENT = 5.0

    @staticmethod
    def analyze_samples(
        samples: list[Any],
        distance_km: float | None = None,
        usable_battery_kwh: float | None = None,
        vehicle_mass_kg: float | None = None,
        drivetrain_efficiency: float | None = None,
        regen_efficiency: float | None = None
    ) -> ElevationImpact:
        clean_samples = ElevationImpactService.clean_samples(
            samples
        )

        if len(clean_samples) < 2:
            return ElevationImpactService.empty_result(
                usable_battery_kwh=usable_battery_kwh,
                distance_km=distance_km,
                warning="Not enough elevation samples to calculate elevation impact."
            )

        vehicle_mass_kg = (
            vehicle_mass_kg
            or ElevationImpactService.DEFAULT_VEHICLE_MASS_KG
        )

        drivetrain_efficiency = (
            drivetrain_efficiency
            or ElevationImpactService.DEFAULT_DRIVETRAIN_EFFICIENCY
        )

        regen_efficiency = (
            regen_efficiency
            or ElevationImpactService.DEFAULT_REGEN_EFFICIENCY
        )

        elevation_gain_m = 0.0
        elevation_loss_m = 0.0

        previous_elevation = clean_samples[0]["elevation_m"]

        for sample in clean_samples[1:]:
            current_elevation = sample["elevation_m"]
            difference = current_elevation - previous_elevation

            if difference > 0:
                elevation_gain_m += difference
            elif difference < 0:
                elevation_loss_m += abs(
                    difference
                )

            previous_elevation = current_elevation

        net_elevation_change_m = (
            clean_samples[-1]["elevation_m"] -
            clean_samples[0]["elevation_m"]
        )

        climb_energy_kwh = (
            vehicle_mass_kg *
            ElevationImpactService.GRAVITY_M_PER_S2 *
            elevation_gain_m /
            ElevationImpactService.JOULES_PER_KWH /
            drivetrain_efficiency
        )

        regen_recovered_kwh = (
            vehicle_mass_kg *
            ElevationImpactService.GRAVITY_M_PER_S2 *
            elevation_loss_m /
            ElevationImpactService.JOULES_PER_KWH *
            regen_efficiency
        )

        net_energy_kwh = (
            climb_energy_kwh -
            regen_recovered_kwh
        )

        soc_impact_percent = (
            ElevationImpactService.calculate_soc_impact_percent(
                net_energy_kwh=net_energy_kwh,
                usable_battery_kwh=usable_battery_kwh
            )
        )

        resolved_distance_km = (
            distance_km
            or clean_samples[-1]["distance_km"]
            or 0.0
        )

        efficiency_impact = (
            ElevationImpactService.calculate_efficiency_impact(
                net_energy_kwh=net_energy_kwh,
                distance_km=resolved_distance_km
            )
        )

        warnings = ElevationImpactService.build_warnings(
            elevation_gain_m=elevation_gain_m,
            soc_impact_percent=soc_impact_percent
        )

        return ElevationImpact(
            elevation_gain_m=round(elevation_gain_m, 1),
            elevation_loss_m=round(elevation_loss_m, 1),
            net_elevation_change_m=round(net_elevation_change_m, 1),
            climb_energy_kwh=round(climb_energy_kwh, 3),
            regen_recovered_kwh=round(regen_recovered_kwh, 3),
            net_energy_kwh=round(net_energy_kwh, 3),
            soc_impact_percent=ElevationImpactService.round_optional(
                soc_impact_percent,
                3
            ),
            efficiency_impact_kwh_per_100km=ElevationImpactService.round_optional(
                efficiency_impact,
                3
            ),
            warnings=warnings
        )

    @staticmethod
    def clean_samples(samples: list[Any]) -> list[dict[str, float]]:
        clean = []

        for sample in samples or []:
            elevation_m = ElevationImpactService.get_value(
                sample,
                "elevation_m"
            )

            if elevation_m is None:
                continue

            distance_km = ElevationImpactService.get_value(
                sample,
                "route_distance_km"
            )

            if distance_km is None:
                distance_km = ElevationImpactService.get_value(
                    sample,
                    "distance_km"
                )

            if distance_km is None:
                distance_km = 0.0

            clean.append(
                {
                    "distance_km": float(distance_km),
                    "elevation_m": float(elevation_m)
                }
            )

        clean.sort(
            key=lambda item: item["distance_km"]
        )

        return clean

    @staticmethod
    def get_value(
        item: Any,
        name: str
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
    def calculate_soc_impact_percent(
        net_energy_kwh: float,
        usable_battery_kwh: float | None
    ) -> float | None:
        if not usable_battery_kwh:
            return None

        if usable_battery_kwh <= 0:
            return None

        return (
            net_energy_kwh /
            usable_battery_kwh
        ) * 100

    @staticmethod
    def calculate_efficiency_impact(
        net_energy_kwh: float,
        distance_km: float | None
    ) -> float | None:
        if not distance_km:
            return None

        if distance_km <= 0:
            return None

        return (
            net_energy_kwh /
            distance_km
        ) * 100

    @staticmethod
    def build_warnings(
        elevation_gain_m: float,
        soc_impact_percent: float | None
    ) -> list[str]:
        warnings = []

        if (
            elevation_gain_m >=
            ElevationImpactService.HIGH_ELEVATION_GAIN_WARNING_M
        ):
            warnings.append(
                "High elevation gain may significantly reduce real-world range."
            )

        if (
            soc_impact_percent is not None and
            soc_impact_percent >=
            ElevationImpactService.HIGH_SOC_IMPACT_WARNING_PERCENT
        ):
            warnings.append(
                "Elevation impact is large enough to materially affect arrival SOC."
            )

        return warnings

    @staticmethod
    def empty_result(
        usable_battery_kwh: float | None,
        distance_km: float | None,
        warning: str | None = None
    ) -> ElevationImpact:
        warnings = []

        if warning:
            warnings.append(
                warning
            )

        return ElevationImpact(
            elevation_gain_m=0.0,
            elevation_loss_m=0.0,
            net_elevation_change_m=0.0,
            climb_energy_kwh=0.0,
            regen_recovered_kwh=0.0,
            net_energy_kwh=0.0,
            soc_impact_percent=ElevationImpactService.calculate_soc_impact_percent(
                net_energy_kwh=0.0,
                usable_battery_kwh=usable_battery_kwh
            ),
            efficiency_impact_kwh_per_100km=ElevationImpactService.calculate_efficiency_impact(
                net_energy_kwh=0.0,
                distance_km=distance_km
            ),
            warnings=warnings
        )

    @staticmethod
    def round_optional(
        value,
        digits
    ):
        if value is None:
            return None

        return round(
            value,
            digits
        )