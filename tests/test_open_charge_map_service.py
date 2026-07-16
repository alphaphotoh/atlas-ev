from backend.services.charging.open_charge_map_service import OpenChargeMapService


def test_open_charge_map_normalizes_poi_record():
    record = {
        "ID": 123,
        "AddressInfo": {
            "Title": "Test Fast Charger",
            "AddressLine1": "123 Main Street",
            "Town": "Pickering",
            "StateOrProvince": "ON",
            "Postcode": "L1V",
            "Latitude": 43.8,
            "Longitude": -79.1,
        },
        "OperatorInfo": {
            "Title": "Test Network",
        },
        "StatusType": {
            "Title": "Operational",
            "IsOperational": True,
        },
        "Connections": [
            {
                "PowerKW": 150,
                "Quantity": 2,
            },
            {
                "PowerKW": 50,
                "Quantity": 1,
            },
        ],
    }

    result = OpenChargeMapService.normalize_poi_record(
        record,
        origin_latitude=43.81,
        origin_longitude=-79.12,
    )

    assert result is not None
    assert result.ocm_id == 123
    assert result.title == "Test Fast Charger"
    assert result.operator == "Test Network"
    assert result.status_title == "Operational"
    assert result.is_operational is True
    assert result.total_stalls == 3
    assert result.max_power_kw == 150
    assert result.distance_km is not None

def test_open_charge_map_api_key_aliases(monkeypatch):
    monkeypatch.delenv("OPEN_CHARGE_MAP_API_KEY", raising=False)
    monkeypatch.delenv("OPENCHARGEMAP_API_KEY", raising=False)

    assert OpenChargeMapService.get_api_key() == ""

    monkeypatch.setenv("OPENCHARGEMAP_API_KEY", "old-style-key")
    assert OpenChargeMapService.get_api_key() == "old-style-key"

    monkeypatch.setenv("OPEN_CHARGE_MAP_API_KEY", "new-style-key")
    assert OpenChargeMapService.get_api_key() == "new-style-key"

