import os
import re
from dataclasses import dataclass

import httpx


@dataclass
class LiveTrafficResult:
    available: bool

    live_duration_minutes: float | None = None
    static_duration_minutes: float | None = None
    distance_km: float | None = None

    provider: str = "google_routes"
    warning: str | None = None


class LiveTrafficService:
    GOOGLE_ROUTES_URL = (
        "https://routes.googleapis.com/directions/v2:computeRoutes"
    )

    @staticmethod
    async def get_live_traffic_for_route(route) -> LiveTrafficResult:
        api_key = LiveTrafficService.get_api_key()

        if not api_key:
            return LiveTrafficResult(
                available=False,
                warning=(
                    "GOOGLE_ROUTES_API_KEY is not configured; "
                    "live traffic fell back to estimated traffic."
                )
            )

        coordinates = getattr(
            route,
            "geometry",
            None
        )

        if not coordinates:
            return LiveTrafficResult(
                available=False,
                warning=(
                    "Route geometry is unavailable; live traffic fell back "
                    "to estimated traffic."
                )
            )

        try:
            origin = LiveTrafficService.first_coordinate(
                coordinates
            )

            destination = LiveTrafficService.last_coordinate(
                coordinates
            )

            payload = LiveTrafficService.build_payload(
                origin=origin,
                destination=destination
            )

            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": (
                    "routes.duration,"
                    "routes.staticDuration,"
                    "routes.distanceMeters"
                )
            }

            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(
                    LiveTrafficService.GOOGLE_ROUTES_URL,
                    json=payload,
                    headers=headers
                )

            if response.status_code >= 400:
                return LiveTrafficResult(
                    available=False,
                    warning=(
                        "Google live traffic request failed with status "
                        f"{response.status_code}; using estimated traffic."
                    )
                )

            data = response.json()
            routes = data.get(
                "routes",
                []
            )

            if not routes:
                return LiveTrafficResult(
                    available=False,
                    warning=(
                        "Google live traffic returned no route; using "
                        "estimated traffic."
                    )
                )

            google_route = routes[0]

            live_seconds = LiveTrafficService.parse_duration_seconds(
                google_route.get(
                    "duration"
                )
            )

            static_seconds = LiveTrafficService.parse_duration_seconds(
                google_route.get(
                    "staticDuration"
                )
            )

            distance_meters = google_route.get(
                "distanceMeters"
            )

            if live_seconds is None or static_seconds is None:
                return LiveTrafficResult(
                    available=False,
                    warning=(
                        "Google live traffic response did not include both "
                        "duration and staticDuration; using estimated traffic."
                    )
                )

            distance_km = None

            if distance_meters is not None:
                distance_km = round(
                    float(distance_meters) / 1000,
                    2
                )

            return LiveTrafficResult(
                available=True,
                live_duration_minutes=round(
                    live_seconds / 60,
                    1
                ),
                static_duration_minutes=round(
                    static_seconds / 60,
                    1
                ),
                distance_km=distance_km
            )

        except Exception as exc:
            return LiveTrafficResult(
                available=False,
                warning=(
                    "Google live traffic lookup failed; using estimated "
                    f"traffic. {type(exc).__name__}: {exc}"
                )
            )

    @staticmethod
    def get_api_key():
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except Exception:
            pass

        return (
            os.getenv("GOOGLE_ROUTES_API_KEY") or
            os.getenv("GOOGLE_MAPS_API_KEY")
        )

    @staticmethod
    def build_payload(
        origin,
        destination
    ):
        return {
            "origin": {
                "location": {
                    "latLng": {
                        "latitude": origin["latitude"],
                        "longitude": origin["longitude"]
                    }
                }
            },
            "destination": {
                "location": {
                    "latLng": {
                        "latitude": destination["latitude"],
                        "longitude": destination["longitude"]
                    }
                }
            },
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
            "computeAlternativeRoutes": False,
            "languageCode": "en-US",
            "units": "METRIC"
        }

    @staticmethod
    def first_coordinate(coordinates):
        return LiveTrafficService.normalize_coordinate(
            coordinates[0]
        )

    @staticmethod
    def last_coordinate(coordinates):
        return LiveTrafficService.normalize_coordinate(
            coordinates[-1]
        )

    @staticmethod
    def normalize_coordinate(coordinate):
        if isinstance(coordinate, dict):
            latitude = (
                coordinate.get("latitude") or
                coordinate.get("lat")
            )

            longitude = (
                coordinate.get("longitude") or
                coordinate.get("lng") or
                coordinate.get("lon")
            )

            return {
                "latitude": float(latitude),
                "longitude": float(longitude)
            }

        if isinstance(coordinate, (list, tuple)) and len(coordinate) >= 2:
            first = float(coordinate[0])
            second = float(coordinate[1])

            # Clear longitude, latitude format.
            if abs(first) > 90 and abs(second) <= 90:
                return {
                    "latitude": second,
                    "longitude": first
                }

            # Clear latitude, longitude format.
            if abs(first) <= 90 and abs(second) > 90:
                return {
                    "latitude": first,
                    "longitude": second
                }

            # Common North America format from ORS/GeoJSON: [negative longitude, positive latitude].
            if first < 0 and second > 0:
                return {
                    "latitude": second,
                    "longitude": first
                }

            # Common latitude, longitude format: [positive latitude, negative longitude].
            if first > 0 and second < 0:
                return {
                    "latitude": first,
                    "longitude": second
                }

            # Fallback: assume latitude, longitude.
            return {
                "latitude": first,
                "longitude": second
            }

        raise ValueError(
            "Unsupported route coordinate format."
        )

    @staticmethod
    def parse_duration_seconds(value):
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value)

        match = re.match(
            r"^([0-9]+(?:\.[0-9]+)?)s$",
            text
        )

        if not match:
            return None

        return float(
            match.group(1)
        )