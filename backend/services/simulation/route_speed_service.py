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