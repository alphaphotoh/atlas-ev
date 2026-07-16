from dataclasses import dataclass


@dataclass
class TrafficImpact:
    applied: bool
    mode: str

    duration_multiplier: float
    extra_duration_minutes: float
    adjusted_duration_minutes: float | None

    efficiency_adjustment_kwh_per_100km: float
    energy_impact_kwh: float
    soc_impact_percent: float | None

    traffic_level: str
    factors: list[str]
    warnings: list[str]


class TrafficImpactService:
    VALID_MODES = {
        "none",
        "estimated",
        "live"
    }

    LEVEL_MULTIPLIERS = {
        "light": 0.65,
        "moderate": 1.0,
        "heavy": 1.55
    }

    @staticmethod
    def build(
        traffic_mode: str | None,
        distance_km: float | None,
        duration_minutes: float | None,
        highway_ratio: float | None,
        usable_battery_kwh: float | None,
        traffic_level: str | None = None
    ) -> TrafficImpact:
        mode = TrafficImpactService.normalize_mode(
            traffic_mode
        )

        distance_km = TrafficImpactService.safe_float(
            distance_km,
            0.0
        )

        duration_minutes = TrafficImpactService.safe_float(
            duration_minutes,
            0.0
        )

        highway_ratio = TrafficImpactService.clamp(
            TrafficImpactService.safe_float(
                highway_ratio,
                0.8
            ),
            0.0,
            1.0
        )

        usable_battery_kwh = TrafficImpactService.safe_float(
            usable_battery_kwh,
            0.0
        )

        level = TrafficImpactService.normalize_level(
            traffic_level
        )

        if mode == "none":
            return TrafficImpactService.empty(
                mode=mode,
                duration_minutes=duration_minutes
            )

        factors = []
        warnings = []

        if mode == "live":
            warnings.append(
                "Live traffic is not connected yet; using estimated traffic adjustment."
            )

        level_multiplier = TrafficImpactService.LEVEL_MULTIPLIERS[level]

        delay_factor = TrafficImpactService.estimated_delay_factor(
            highway_ratio=highway_ratio,
            level_multiplier=level_multiplier
        )

        efficiency_adjustment = TrafficImpactService.estimated_efficiency_adjustment(
            highway_ratio=highway_ratio,
            level_multiplier=level_multiplier
        )

        extra_duration = duration_minutes * delay_factor
        adjusted_duration = duration_minutes + extra_duration

        energy_impact = (
            distance_km *
            efficiency_adjustment /
            100
        )

        soc_impact = TrafficImpactService.soc_impact(
            energy_kwh=energy_impact,
            usable_battery_kwh=usable_battery_kwh
        )

        factors.append(
            f"Traffic mode: {mode}"
        )

        factors.append(
            f"Traffic level: {level}"
        )

        if highway_ratio >= 0.75:
            factors.append(
                "Mostly highway route"
            )

        elif highway_ratio <= 0.4:
            factors.append(
                "More city or mixed driving"
            )

        else:
            factors.append(
                "Mixed highway/city route"
            )

        return TrafficImpact(
            applied=True,
            mode=mode,
            duration_multiplier=round(
                1 + delay_factor,
                3
            ),
            extra_duration_minutes=round(
                extra_duration,
                1
            ),
            adjusted_duration_minutes=round(
                adjusted_duration,
                1
            ),
            efficiency_adjustment_kwh_per_100km=round(
                efficiency_adjustment,
                2
            ),
            energy_impact_kwh=round(
                energy_impact,
                2
            ),
            soc_impact_percent=TrafficImpactService.round_optional(
                soc_impact
            ),
            traffic_level=level,
            factors=TrafficImpactService.unique_list(
                factors
            ),
            warnings=TrafficImpactService.unique_list(
                warnings
            )
        )

    @staticmethod
    def build_from_live_result(
        traffic_mode: str | None,
        distance_km: float | None,
        duration_minutes: float | None,
        highway_ratio: float | None,
        usable_battery_kwh: float | None,
        live_result
    ) -> TrafficImpact:
        mode = TrafficImpactService.normalize_mode(
            traffic_mode
        )

        if mode != "live":
            return TrafficImpactService.build(
                traffic_mode=traffic_mode,
                distance_km=distance_km,
                duration_minutes=duration_minutes,
                highway_ratio=highway_ratio,
                usable_battery_kwh=usable_battery_kwh
            )

        if not getattr(
            live_result,
            "available",
            False
        ):
            fallback = TrafficImpactService.build(
                traffic_mode="live",
                traffic_level="moderate",
                distance_km=distance_km,
                duration_minutes=duration_minutes,
                highway_ratio=highway_ratio,
                usable_battery_kwh=usable_battery_kwh
            )

            warning = getattr(
                live_result,
                "warning",
                None
            )

            if warning and warning not in fallback.warnings:
                fallback.warnings.append(
                    warning
                )

            return fallback

        atlas_duration = TrafficImpactService.safe_float(
            duration_minutes,
            0.0
        )

        live_duration = TrafficImpactService.safe_float(
            getattr(
                live_result,
                "live_duration_minutes",
                None
            ),
            0.0
        )

        static_duration = TrafficImpactService.safe_float(
            getattr(
                live_result,
                "static_duration_minutes",
                None
            ),
            0.0
        )

        if atlas_duration <= 0 or live_duration <= 0 or static_duration <= 0:
            return TrafficImpactService.build(
                traffic_mode="live",
                traffic_level="moderate",
                distance_km=distance_km,
                duration_minutes=duration_minutes,
                highway_ratio=highway_ratio,
                usable_battery_kwh=usable_battery_kwh
            )

        duration_multiplier = max(
            live_duration / static_duration,
            1.0
        )

        extra_duration = atlas_duration * (
            duration_multiplier - 1
        )

        adjusted_duration = atlas_duration + extra_duration

        live_delay_ratio = max(
            duration_multiplier - 1,
            0.0
        )

        if live_delay_ratio >= 0.15:
            level = "heavy"

        elif live_delay_ratio >= 0.07:
            level = "moderate"

        else:
            level = "light"

        highway_ratio = TrafficImpactService.clamp(
            TrafficImpactService.safe_float(
                highway_ratio,
                0.8
            ),
            0.0,
            1.0
        )

        distance_km = TrafficImpactService.safe_float(
            distance_km,
            0.0
        )

        usable_battery_kwh = TrafficImpactService.safe_float(
            usable_battery_kwh,
            0.0
        )

        estimated_delay = TrafficImpactService.estimated_delay_factor(
            highway_ratio=highway_ratio,
            level_multiplier=TrafficImpactService.LEVEL_MULTIPLIERS[level]
        )

        if estimated_delay <= 0:
            estimated_delay = 0.01

        scale = TrafficImpactService.clamp(
            live_delay_ratio / estimated_delay,
            0.25,
            2.5
        )

        efficiency_adjustment = (
            TrafficImpactService.estimated_efficiency_adjustment(
                highway_ratio=highway_ratio,
                level_multiplier=TrafficImpactService.LEVEL_MULTIPLIERS[level]
            ) *
            scale
        )

        energy_impact = (
            distance_km *
            efficiency_adjustment /
            100
        )

        soc_impact = TrafficImpactService.soc_impact(
            energy_kwh=energy_impact,
            usable_battery_kwh=usable_battery_kwh
        )

        factors = [
            "Traffic mode: live",
            "Traffic provider: Google Routes",
            f"Live traffic level: {level}",
            f"Google live duration: {round(live_duration, 1)} min",
            f"Google static duration: {round(static_duration, 1)} min"
        ]

        return TrafficImpact(
            applied=True,
            mode="live",
            duration_multiplier=round(
                duration_multiplier,
                3
            ),
            extra_duration_minutes=round(
                extra_duration,
                1
            ),
            adjusted_duration_minutes=round(
                adjusted_duration,
                1
            ),
            efficiency_adjustment_kwh_per_100km=round(
                efficiency_adjustment,
                2
            ),
            energy_impact_kwh=round(
                energy_impact,
                2
            ),
            soc_impact_percent=TrafficImpactService.round_optional(
                soc_impact
            ),
            traffic_level=level,
            factors=TrafficImpactService.unique_list(
                factors
            ),
            warnings=[]
        )

    @staticmethod
    def estimated_delay_factor(
        highway_ratio: float,
        level_multiplier: float
    ) -> float:
        city_ratio = 1 - highway_ratio

        base_delay = (
            highway_ratio * 0.06 +
            city_ratio * 0.18
        )

        return base_delay * level_multiplier

    @staticmethod
    def estimated_efficiency_adjustment(
        highway_ratio: float,
        level_multiplier: float
    ) -> float:
        city_ratio = 1 - highway_ratio

        base_adjustment = (
            highway_ratio * 0.35 +
            city_ratio * 1.4
        )

        return base_adjustment * level_multiplier

    @staticmethod
    def empty(
        mode: str,
        duration_minutes: float
    ) -> TrafficImpact:
        return TrafficImpact(
            applied=False,
            mode=mode,
            duration_multiplier=1.0,
            extra_duration_minutes=0.0,
            adjusted_duration_minutes=round(
                duration_minutes,
                1
            ),
            efficiency_adjustment_kwh_per_100km=0.0,
            energy_impact_kwh=0.0,
            soc_impact_percent=0.0,
            traffic_level="none",
            factors=[],
            warnings=[]
        )

    @staticmethod
    def normalize_mode(
        traffic_mode: str | None
    ) -> str:
        if not traffic_mode:
            return "none"

        mode = str(
            traffic_mode
        ).strip().lower()

        if mode not in TrafficImpactService.VALID_MODES:
            return "none"

        return mode

    @staticmethod
    def normalize_level(
        traffic_level: str | None
    ) -> str:
        if not traffic_level:
            return "moderate"

        level = str(
            traffic_level
        ).strip().lower()

        if level not in TrafficImpactService.LEVEL_MULTIPLIERS:
            return "moderate"

        return level

    @staticmethod
    def soc_impact(
        energy_kwh: float,
        usable_battery_kwh: float
    ) -> float | None:
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
    ) -> float:
        if value is None:
            return default_value

        try:
            return float(
                value
            )

        except (TypeError, ValueError):
            return default_value

    @staticmethod
    def clamp(
        value: float,
        minimum: float,
        maximum: float
    ) -> float:
        return max(
            minimum,
            min(
                value,
                maximum
            )
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

    @staticmethod
    def unique_list(values):
        unique = []

        for value in values:
            if value not in unique:
                unique.append(
                    value
                )

        return unique