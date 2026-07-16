from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from backend.services.charging.open_charge_map_service import (
    OpenChargeMapMatch,
    OpenChargeMapService,
)


@dataclass
class ChargerAvailability:
    status: str = "unknown"
    is_live: bool = False
    available_stalls: int | None = None
    occupied_stalls: int | None = None
    total_stalls: int | None = None
    occupancy_percent: float | None = None
    confidence: str = "low"
    source: str = "No live availability provider connected"
    last_updated: str | None = None
    recommendation: str = (
        "Availability is unknown. Keep a backup charger in the plan."
    )


class ChargerAvailabilityService:
    """
    Live-ready charger availability service.

    unknown:
      honest default, no external provider

    estimated:
      demo/testing occupancy only

    openchargemap:
      free Open Charge Map metadata lookup.
      This improves station metadata/status matching, but it is not live occupancy.
    """

    @staticmethod
    def get_availability(charger: Any) -> ChargerAvailability:
        mode = os.getenv("CHARGER_AVAILABILITY_MODE", "unknown").strip().lower()

        if mode in {"openchargemap", "ocm"}:
            ocm_match = OpenChargeMapService.find_near_charger(charger)

            if ocm_match:
                return ChargerAvailabilityService._from_open_charge_map(
                    ocm_match
                )

            return ChargerAvailability(
                status="unknown",
                is_live=False,
                confidence="low",
                source="Open Charge Map not matched or API key missing",
                recommendation=(
                    "Could not match this charger to Open Charge Map. "
                    "Keep a backup charger in the plan."
                ),
            )

        if mode == "estimated":
            return ChargerAvailabilityService._estimated_availability(charger)

        return ChargerAvailability()

    @staticmethod
    def _from_open_charge_map(
        match: OpenChargeMapMatch,
    ) -> ChargerAvailability:
        now = datetime.now(timezone.utc).isoformat()

        source_parts = ["Open Charge Map metadata"]

        if match.operator:
            source_parts.append(match.operator)

        if match.status_title:
            source_parts.append(match.status_title)

        source = " · ".join(source_parts)

        if match.is_operational is False:
            return ChargerAvailability(
                status="offline",
                is_live=False,
                available_stalls=0,
                occupied_stalls=None,
                total_stalls=match.total_stalls,
                occupancy_percent=None,
                confidence="metadata",
                source=source,
                last_updated=now,
                recommendation=(
                    "Open Charge Map metadata indicates this station may not "
                    "be operational. Prefer a backup charger."
                ),
            )

        return ChargerAvailability(
            status="unknown",
            is_live=False,
            available_stalls=None,
            occupied_stalls=None,
            total_stalls=match.total_stalls,
            occupancy_percent=None,
            confidence="metadata",
            source=source,
            last_updated=now,
            recommendation=(
                "Station metadata was matched from Open Charge Map, but live "
                "stall occupancy is not available from this free feed."
            ),
        )

    @staticmethod
    def _estimated_availability(charger: Any) -> ChargerAvailability:
        name = ChargerAvailabilityService._first_string(
            charger,
            ["name", "charger_name", "station_name", "address"],
        )

        total_stalls = ChargerAvailabilityService._first_int(
            charger,
            [
                "total_stalls",
                "stall_count",
                "num_stalls",
                "connector_count",
                "ports",
                "number_of_chargers",
            ],
        )

        if total_stalls is None or total_stalls <= 0:
            total_stalls = 2

        seed = f"{name}-{datetime.now(timezone.utc).strftime('%Y-%m-%d-%H')}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        value = int(digest[:8], 16)

        occupied_stalls = value % (total_stalls + 1)
        available_stalls = max(total_stalls - occupied_stalls, 0)
        occupancy_percent = round((occupied_stalls / total_stalls) * 100, 1)

        if available_stalls <= 0:
            status = "busy"
            recommendation = (
                "Estimated busy. Consider a backup charger before relying "
                "on this stop."
            )
        elif available_stalls == 1:
            status = "limited"
            recommendation = (
                "Estimated limited availability. Keep the backup charger ready."
            )
        else:
            status = "available"
            recommendation = "Estimated availability looks acceptable."

        return ChargerAvailability(
            status=status,
            is_live=False,
            available_stalls=available_stalls,
            occupied_stalls=occupied_stalls,
            total_stalls=total_stalls,
            occupancy_percent=occupancy_percent,
            confidence="estimated",
            source="Estimated availability model",
            last_updated=datetime.now(timezone.utc).isoformat(),
            recommendation=recommendation,
        )

    @staticmethod
    def _read_value(source: Any, key: str) -> Any:
        if isinstance(source, dict):
            return source.get(key)

        return getattr(source, key, None)

    @staticmethod
    def _first_string(source: Any, keys: list[str]) -> str:
        for key in keys:
            value = ChargerAvailabilityService._read_value(source, key)

            if isinstance(value, str) and value.strip():
                return value.strip()

        return "unknown charger"

    @staticmethod
    def _first_int(source: Any, keys: list[str]) -> int | None:
        for key in keys:
            value = ChargerAvailabilityService._read_value(source, key)

            if isinstance(value, int):
                return value

            if isinstance(value, float):
                return int(value)

            if isinstance(value, str):
                try:
                    return int(float(value))
                except ValueError:
                    continue

            if isinstance(value, list):
                return len(value)

        return None