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
        route: Any,
        highway_ratio: float | None,
    ) -> float | None:
        distance_km = RouteSpeedService._read_float(
            route,
            ["distance_km", "distance"],
        )

        duration_minutes = RouteSpeedService._read_float(
            route,
            ["duration_minutes", "duration"],
        )

        if distance_km is None or duration_minutes is None:
            return None

        if distance_km < RouteSpeedService.LONG_HIGHWAY_MIN_DISTANCE_KM:
            return None

        if highway_ratio is None:
            return None

        if float(highway_ratio) < RouteSpeedService.LONG_HIGHWAY_MIN_RATIO:
            return None

        if duration_minutes <= 0:
            return None

        current_speed = distance_km / (duration_minutes / 60.0)

        if current_speed >= RouteSpeedService.LONG_HIGHWAY_TARGET_SPEED_KMH:
            return None

        normalized_duration = (
            distance_km
            / RouteSpeedService.LONG_HIGHWAY_TARGET_SPEED_KMH
            * 60.0
        )

        gain_minutes = duration_minutes - normalized_duration

        if gain_minutes < RouteSpeedService.LONG_HIGHWAY_MIN_GAIN_MINUTES:
            return None

        normalized_duration = round(
            normalized_duration,
            1,
        )

        metadata = {
            "applied": True,
            "source": "long_highway_fastest_duration",
            "distance_km": round(distance_km, 1),
            "highway_ratio": round(float(highway_ratio), 3),
            "original_duration_minutes": round(duration_minutes, 1),
            "normalized_duration_minutes": normalized_duration,
            "original_average_speed_kmh": round(current_speed, 1),
            "target_average_speed_kmh": RouteSpeedService.LONG_HIGHWAY_TARGET_SPEED_KMH,
            "duration_reduction_minutes": round(gain_minutes, 1),
        }

        try:
            if isinstance(route, dict):
                route["duration_normalization"] = metadata
            else:
                setattr(
                    route,
                    "duration_normalization",
                    metadata,
                )
        except Exception:
            pass

        return normalized_duration

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
