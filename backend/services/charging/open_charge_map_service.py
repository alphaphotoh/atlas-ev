from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class OpenChargeMapMatch:
    ocm_id: int | None
    title: str | None
    operator: str | None
    address: str | None
    latitude: float | None
    longitude: float | None
    distance_km: float | None
    status_title: str | None
    is_operational: bool | None
    total_stalls: int | None
    max_power_kw: float | None


class OpenChargeMapService:
    BASE_URL = "https://api.openchargemap.io/v3"
    CACHE_TTL_SECONDS = 3600
    _cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}

    @staticmethod
    def find_near_charger(
        charger: Any,
        radius_km: float = 2.0,
        max_results: int = 8,
    ) -> OpenChargeMapMatch | None:
        api_key = os.getenv("OPEN_CHARGE_MAP_API_KEY", "").strip()

        if not api_key:
            return None

        latitude = OpenChargeMapService._first_float(
            charger,
            ["latitude", "lat", "charger_latitude"],
        )
        longitude = OpenChargeMapService._first_float(
            charger,
            ["longitude", "lon", "lng", "charger_longitude"],
        )

        if latitude is None or longitude is None:
            return None

        records = OpenChargeMapService._query_nearby(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            max_results=max_results,
            api_key=api_key,
        )

        if not records:
            return None

        charger_name = OpenChargeMapService._first_string(
            charger,
            ["name", "charger_name", "station_name"],
        )
        charger_network = OpenChargeMapService._first_string(
            charger,
            ["network", "operator", "provider"],
        )

        matches = [
            OpenChargeMapService.normalize_poi_record(record, latitude, longitude)
            for record in records
        ]

        matches = [match for match in matches if match is not None]

        if not matches:
            return None

        return sorted(
            matches,
            key=lambda match: OpenChargeMapService._match_score(
                match,
                charger_name,
                charger_network,
            ),
        )[0]

    @staticmethod
    def normalize_poi_record(
        record: dict[str, Any],
        origin_latitude: float | None = None,
        origin_longitude: float | None = None,
    ) -> OpenChargeMapMatch | None:
        address_info = OpenChargeMapService._as_dict(record.get("AddressInfo"))
        operator_info = OpenChargeMapService._as_dict(record.get("OperatorInfo"))
        status_type = OpenChargeMapService._as_dict(record.get("StatusType"))
        connections = record.get("Connections")

        if not isinstance(connections, list):
            connections = []

        latitude = OpenChargeMapService._to_float(address_info.get("Latitude"))
        longitude = OpenChargeMapService._to_float(address_info.get("Longitude"))

        distance_km = OpenChargeMapService._to_float(address_info.get("Distance"))

        if (
            distance_km is None
            and origin_latitude is not None
            and origin_longitude is not None
            and latitude is not None
            and longitude is not None
        ):
            distance_km = OpenChargeMapService._haversine_km(
                origin_latitude,
                origin_longitude,
                latitude,
                longitude,
            )

        title = OpenChargeMapService._clean_string(address_info.get("Title"))
        operator = OpenChargeMapService._clean_string(operator_info.get("Title"))
        status_title = OpenChargeMapService._clean_string(status_type.get("Title"))

        is_operational = status_type.get("IsOperational")
        if not isinstance(is_operational, bool):
            is_operational = None

        total_stalls = OpenChargeMapService._connection_count(connections)
        max_power_kw = OpenChargeMapService._max_power_kw(connections)

        return OpenChargeMapMatch(
            ocm_id=OpenChargeMapService._to_int(record.get("ID")),
            title=title,
            operator=operator,
            address=OpenChargeMapService._format_address(address_info),
            latitude=latitude,
            longitude=longitude,
            distance_km=distance_km,
            status_title=status_title,
            is_operational=is_operational,
            total_stalls=total_stalls,
            max_power_kw=max_power_kw,
        )

    @staticmethod
    def _query_nearby(
        latitude: float,
        longitude: float,
        radius_km: float,
        max_results: int,
        api_key: str,
    ) -> list[dict[str, Any]]:
        cache_key = (
            f"{round(latitude, 4)}:{round(longitude, 4)}:"
            f"{round(radius_km, 1)}:{max_results}"
        )

        cached = OpenChargeMapService._cache.get(cache_key)
        now = time.time()

        if cached and now - cached[0] < OpenChargeMapService.CACHE_TTL_SECONDS:
            return cached[1]

        params = {
            "output": "json",
            "latitude": latitude,
            "longitude": longitude,
            "distance": radius_km,
            "distanceunit": "KM",
            "maxresults": max_results,
            "compact": "false",
            "verbose": "false",
        }

        headers = {
            "X-API-Key": api_key,
            "User-Agent": "AtlasEVTripPlanner/0.1",
        }

        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.get(
                    f"{OpenChargeMapService.BASE_URL}/poi/",
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
        except Exception:
            return []

        if not isinstance(data, list):
            return []

        records = [
            item for item in data
            if isinstance(item, dict)
        ]

        OpenChargeMapService._cache[cache_key] = (now, records)

        return records

    @staticmethod
    def _match_score(
        match: OpenChargeMapMatch,
        charger_name: str | None,
        charger_network: str | None,
    ) -> float:
        score = match.distance_km if match.distance_km is not None else 99.0

        match_title = (match.title or "").lower()
        match_operator = (match.operator or "").lower()

        if charger_name:
            name = charger_name.lower()

            if name in match_title or match_title in name:
                score -= 0.5

        if charger_network:
            network = charger_network.lower()

            if network in match_operator or match_operator in network:
                score -= 0.35

        return score

    @staticmethod
    def _read_value(source: Any, key: str) -> Any:
        if isinstance(source, dict):
            return source.get(key)

        return getattr(source, key, None)

    @staticmethod
    def _first_float(source: Any, keys: list[str]) -> float | None:
        for key in keys:
            value = OpenChargeMapService._read_value(source, key)
            parsed = OpenChargeMapService._to_float(value)

            if parsed is not None:
                return parsed

        return None

    @staticmethod
    def _first_string(source: Any, keys: list[str]) -> str | None:
        for key in keys:
            value = OpenChargeMapService._read_value(source, key)
            parsed = OpenChargeMapService._clean_string(value)

            if parsed:
                return parsed

        return None

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _clean_string(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()

        if isinstance(value, (int, float)):
            return str(value)

        return None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            parsed = float(value)
            return parsed if math.isfinite(parsed) else None

        if isinstance(value, str):
            try:
                parsed = float(value)
                return parsed if math.isfinite(parsed) else None
            except ValueError:
                return None

        return None

    @staticmethod
    def _to_int(value: Any) -> int | None:
        parsed = OpenChargeMapService._to_float(value)

        if parsed is None:
            return None

        return int(parsed)

    @staticmethod
    def _connection_count(connections: list[Any]) -> int | None:
        total = 0

        for connection in connections:
            if not isinstance(connection, dict):
                continue

            quantity = OpenChargeMapService._to_int(connection.get("Quantity"))

            if quantity is None or quantity <= 0:
                total += 1
            else:
                total += quantity

        return total if total > 0 else None

    @staticmethod
    def _max_power_kw(connections: list[Any]) -> float | None:
        values: list[float] = []

        for connection in connections:
            if not isinstance(connection, dict):
                continue

            power_kw = OpenChargeMapService._to_float(connection.get("PowerKW"))

            if power_kw is not None and power_kw > 0:
                values.append(power_kw)

        return max(values) if values else None

    @staticmethod
    def _format_address(address_info: dict[str, Any]) -> str | None:
        parts = [
            OpenChargeMapService._clean_string(address_info.get("AddressLine1")),
            OpenChargeMapService._clean_string(address_info.get("Town")),
            OpenChargeMapService._clean_string(address_info.get("StateOrProvince")),
            OpenChargeMapService._clean_string(address_info.get("Postcode")),
        ]

        clean_parts = [part for part in parts if part]

        return ", ".join(clean_parts) if clean_parts else None

    @staticmethod
    def _haversine_km(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        radius_km = 6371.0

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1)
            * math.cos(phi2)
            * math.sin(delta_lambda / 2) ** 2
        )

        return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))