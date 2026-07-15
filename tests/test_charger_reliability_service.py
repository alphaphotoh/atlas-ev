from types import SimpleNamespace

from backend.services.planning.charger_reliability_service import (
    ChargerReliabilityService,
)


def charger(
    network="Petro-Canada",
    power_kw=350,
    detour_distance_km=0.2
):
    return SimpleNamespace(
        network=network,
        power_kw=power_kw,
        detour_distance_km=detour_distance_km
    )


def test_high_power_close_charger_gets_high_reliability():
    result = ChargerReliabilityService.score_charger(
        charger()
    )

    assert result["reliability_score"] >= 85
    assert result["reliability_label"] == "High"
    assert result["availability_status"] == "unknown"
    assert result["is_live_availability"] is False


def test_unknown_low_power_charger_is_lower_score():
    result = ChargerReliabilityService.score_charger(
        charger(
            network="Unknown Network",
            power_kw=50,
            detour_distance_km=4.0
        )
    )

    assert result["reliability_score"] < 70
    assert result["reliability_label"] == "Low"
    assert any(
        "backup" in note.lower()
        for note in result["reliability_notes"]
    )


def test_medium_charger_gets_medium_or_high_score():
    result = ChargerReliabilityService.score_charger(
        charger(
            network="IVY",
            power_kw=150,
            detour_distance_km=1.0
        )
    )

    assert result["reliability_score"] >= 70
    assert result["reliability_label"] in [
        "Medium",
        "High"
    ]


def test_missing_power_is_safe():
    result = ChargerReliabilityService.score_charger(
        charger(
            network="ChargePoint",
            power_kw=None,
            detour_distance_km=0.4
        )
    )

    assert result["reliability_score"] > 0
    assert result["availability_status"] == "unknown"
    assert any(
        "power is unknown" in note.lower()
        for note in result["reliability_notes"]
    )