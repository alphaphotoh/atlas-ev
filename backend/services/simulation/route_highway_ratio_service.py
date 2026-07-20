from dataclasses import dataclass


@dataclass
class RouteHighwayRatioEstimate:
    highway_ratio: float
    average_speed_kmh: float | None
    source: str
    notes: list[str]


class RouteHighwayRatioService:
    @staticmethod
    def estimate(
        route,
        fallback_highway_ratio: float | None = None,
    ) -> RouteHighwayRatioEstimate:
        distance_km = RouteHighwayRatioService.read_float(
            route,
            ["distance_km", "distance"],
        )

        duration_minutes = RouteHighwayRatioService.read_float(
            route,
            ["duration_minutes", "duration"],
        )

        fallback = RouteHighwayRatioService.clamp(
            fallback_highway_ratio,
            0.0,
            1.0,
            0.8,
        )

        if (
            distance_km is None
            or duration_minutes is None
            or distance_km <= 0
            or duration_minutes <= 0
        ):
            return RouteHighwayRatioEstimate(
                highway_ratio=fallback,
                average_speed_kmh=None,
                source="fallback_highway_ratio",
                notes=[
                    "Route distance/duration unavailable; used fallback highway ratio.",
                ],
            )

        average_speed_kmh = distance_km / (duration_minutes / 60.0)

        highway_ratio = RouteHighwayRatioService.estimate_from_speed_and_distance(
            distance_km=distance_km,
            average_speed_kmh=average_speed_kmh,
        )

        notes = [
            "Highway ratio estimated automatically from route distance and route duration.",
            f"Route average speed: {round(average_speed_kmh, 1)} km/h.",
        ]

        if highway_ratio >= 0.8:
            notes.append("Route appears mostly highway.")
        elif highway_ratio <= 0.45:
            notes.append("Route appears mostly urban/local.")
        else:
            notes.append("Route appears mixed highway and city.")

        return RouteHighwayRatioEstimate(
            highway_ratio=highway_ratio,
            average_speed_kmh=round(
                average_speed_kmh,
                1,
            ),
            source="route_distance_and_duration",
            notes=notes,
        )

    @staticmethod
    def estimate_from_speed_and_distance(
        distance_km: float,
        average_speed_kmh: float,
    ) -> float:
        if average_speed_kmh >= 95:
            ratio = 0.92
        elif average_speed_kmh >= 88:
            ratio = 0.86
        elif average_speed_kmh >= 80:
            ratio = 0.78
        elif average_speed_kmh >= 70:
            ratio = 0.68
        elif average_speed_kmh >= 60:
            ratio = 0.55
        elif average_speed_kmh >= 45:
            ratio = 0.40
        else:
            ratio = 0.25

        if distance_km >= 1000 and average_speed_kmh >= 75:
            ratio = max(
                ratio,
                0.88,
            )
        elif distance_km >= 500 and average_speed_kmh >= 70:
            ratio = max(
                ratio,
                0.82,
            )
        elif distance_km >= 250 and average_speed_kmh >= 65:
            ratio = max(
                ratio,
                0.75,
            )
        elif distance_km <= 40 and average_speed_kmh <= 60:
            ratio = min(
                ratio,
                0.45,
            )

        return round(
            RouteHighwayRatioService.clamp(
                ratio,
                0.05,
                0.95,
                0.8,
            ),
            2,
        )

    @staticmethod
    def read_float(
        obj,
        names,
    ):
        for name in names:
            value = getattr(
                obj,
                name,
                None,
            )

            if value is None and isinstance(obj, dict):
                value = obj.get(
                    name,
                )

            if value is None:
                continue

            try:
                return float(
                    value,
                )
            except Exception:
                continue

        return None

    @staticmethod
    def clamp(
        value,
        minimum,
        maximum,
        default,
    ):
        try:
            value = float(
                value,
            )
        except Exception:
            value = default

        return max(
            minimum,
            min(
                maximum,
                value,
            ),
        )
