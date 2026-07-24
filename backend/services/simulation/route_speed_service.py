from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RouteSpeedEstimate:
    average_speed_kmh: float
    source: str
    confidence: str
    distance_km: float | None
    duration_minutes: float | None
    fallback_used: bool


class RouteSpeedService:
    MIN_REASONABLE_SPEED_KMH = 20.0
    MAX_REASONABLE_SPEED_KMH = 130.0
    DEFAULT_SPEED_KMH = 90.0

    LONG_HIGHWAY_MIN_DISTANCE_KM = 650.0
    LONG_HIGHWAY_MIN_RATIO = 0.70
    LONG_HIGHWAY_TARGET_SPEED_KMH = 91.0
    LONG_HIGHWAY_MIN_GAIN_MINUTES = 10.0

    @staticmethod
    def estimate(
        route: Any,
        fallback_average_speed_kmh: float | None = None,
    ) -> RouteSpeedEstimate:
        distance_km = RouteSpeedService._read_float(
            route,
            ["distance_km", "distance"],
        )

        duration_minutes = RouteSpeedService._read_float(
            route,
            ["duration_minutes", "duration"],
        )

        route_speed = RouteSpeedService._speed_from_route(
            distance_km=distance_km,
            duration_minutes=duration_minutes,
        )

        if route_speed is not None:
            return RouteSpeedEstimate(
                average_speed_kmh=route_speed,
                source="route_distance_and_duration",
                confidence="high",
                distance_km=distance_km,
                duration_minutes=duration_minutes,
                fallback_used=False,
            )

        fallback_speed = RouteSpeedService._normalize_speed(
            fallback_average_speed_kmh
        )

        return RouteSpeedEstimate(
            average_speed_kmh=fallback_speed,
            source="fallback_average_speed",
            confidence="low",
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            fallback_used=True,
        )

    @staticmethod
    def apply_long_highway_duration_normalization(
        route,
        highway_ratio,
        target_speed_kmh: float | None = None,
    ):
        distance_km = getattr(
            route,
            "distance_km",
            0.0,
        ) or 0.0

        original_duration_minutes = getattr(
            route,
            "duration_minutes",
            0.0,
        ) or 0.0

        if distance_km <= 0 or original_duration_minutes <= 0:
            return

        try:
            highway_ratio = float(highway_ratio or 0.0)
        except Exception:
            highway_ratio = 0.0

        highway_ratio = max(
            0.0,
            min(
                1.0,
                highway_ratio,
            ),
        )

        minimum_distance_km = getattr(
            RouteSpeedService,
            "LONG_HIGHWAY_MIN_DISTANCE_KM",
            300.0,
        )

        minimum_highway_ratio = getattr(
            RouteSpeedService,
            "LONG_HIGHWAY_MIN_HIGHWAY_RATIO",
            getattr(
                RouteSpeedService,
                "LONG_HIGHWAY_MIN_RATIO",
                0.65,
            ),
        )

        if distance_km < minimum_distance_km:
            return

        if highway_ratio < minimum_highway_ratio:
            return

        highway_speed_kmh = RouteSpeedService._normalize_highway_target_speed(
            target_speed_kmh
        )

        local_road_speed_kmh = getattr(
            RouteSpeedService,
            "LONG_TRIP_LOCAL_ROAD_SPEED_KMH",
            60.0,
        )

        try:
            local_road_speed_kmh = float(local_road_speed_kmh)
        except Exception:
            local_road_speed_kmh = 60.0

        local_road_speed_kmh = max(
            35.0,
            min(
                80.0,
                local_road_speed_kmh,
            ),
        )

        highway_distance_km = distance_km * highway_ratio
        local_distance_km = distance_km - highway_distance_km

        highway_minutes = (
            highway_distance_km
            / highway_speed_kmh
        ) * 60.0

        local_minutes = (
            local_distance_km
            / local_road_speed_kmh
        ) * 60.0

        adjusted_duration_minutes = round(
            highway_minutes + local_minutes,
            1,
        )

        if adjusted_duration_minutes <= 0:
            return

        adjusted_average_speed_kmh = round(
            distance_km / (adjusted_duration_minutes / 60.0),
            1,
        )

        metadata = getattr(
            route,
            "metadata",
            None,
        )

        if metadata is None or not isinstance(metadata, dict):
            metadata = {}
            try:
                route.metadata = metadata
            except Exception:
                pass

        metadata["highway_speed_normalization"] = {
            "source": "user_highway_speed_only",
            "highway_speed_kmh": highway_speed_kmh,
            "local_road_speed_kmh": local_road_speed_kmh,
            "highway_ratio": round(highway_ratio, 3),
            "highway_distance_km": round(highway_distance_km, 1),
            "local_distance_km": round(local_distance_km, 1),
            "original_duration_minutes": round(
                original_duration_minutes,
                1,
            ),
            "adjusted_duration_minutes": adjusted_duration_minutes,
            "adjusted_average_speed_kmh": adjusted_average_speed_kmh,
            "duration_delta_minutes": round(
                adjusted_duration_minutes - original_duration_minutes,
                1,
            ),
        }

        route.duration_minutes = adjusted_duration_minutes

    @staticmethod
    def _normalize_highway_target_speed(
        value: float | None,
    ) -> float:
        if value is None:
            return RouteSpeedService.LONG_HIGHWAY_TARGET_SPEED_KMH

        try:
            speed = float(value)
        except Exception:
            return RouteSpeedService.LONG_HIGHWAY_TARGET_SPEED_KMH

        if speed <= 0:
            return RouteSpeedService.LONG_HIGHWAY_TARGET_SPEED_KMH

        return round(
            max(
                75.0,
                min(
                    125.0,
                    speed,
                ),
            ),
            1,
        )

    @staticmethod
    def _speed_from_route(
        distance_km: float | None,
        duration_minutes: float | None,
    ) -> float | None:
        if distance_km is None or duration_minutes is None:
            return None

        if distance_km <= 0 or duration_minutes <= 0:
            return None

        speed = distance_km / (duration_minutes / 60.0)

        if speed < RouteSpeedService.MIN_REASONABLE_SPEED_KMH:
            return None

        if speed > RouteSpeedService.MAX_REASONABLE_SPEED_KMH:
            return None

        return round(speed, 1)

    @staticmethod
    def _normalize_speed(value: float | None) -> float:
        if value is None or value <= 0:
            return RouteSpeedService.DEFAULT_SPEED_KMH

        return round(
            max(
                RouteSpeedService.MIN_REASONABLE_SPEED_KMH,
                min(RouteSpeedService.MAX_REASONABLE_SPEED_KMH, float(value)),
            ),
            1,
        )

    @staticmethod
    def _read_float(source: Any, keys: list[str]) -> float | None:
        for key in keys:
            if isinstance(source, dict):
                value = source.get(key)
            else:
                value = getattr(source, key, None)

            if isinstance(value, bool):
                continue

            if isinstance(value, (int, float)):
                return float(value)

            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    continue

        return None
