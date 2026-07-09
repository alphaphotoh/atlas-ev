import csv
import io


class CsvTemplateService:
    FILENAME = "atlas_ev_learning_template.csv"

    HEADERS = [
        "vehicle_id",
        "trip_date",
        "origin",
        "destination",
        "distance_km",
        "starting_soc",
        "ending_soc",
        "charged_energy_kwh",
        "actual_energy_used_kwh",
        "predicted_efficiency_kwh_per_100km",
        "predicted_energy_used_kwh",
        "outside_temperature_c",
        "average_speed_kmh",
        "highway_ratio",
        "climate_control",
        "tire_pressure_note",
        "payload_note",
        "notes"
    ]

    SAMPLE_ROWS = [
        {
            "vehicle_id": "vf9",
            "trip_date": "2026-07-10",
            "origin": "Pickering, ON",
            "destination": "Chicago, IL",
            "distance_km": 859.1,
            "starting_soc": 100,
            "ending_soc": 25.3,
            "charged_energy_kwh": 0,
            "actual_energy_used_kwh": 285,
            "predicted_efficiency_kwh_per_100km": 31.7,
            "predicted_energy_used_kwh": 272.3,
            "outside_temperature_c": 22,
            "average_speed_kmh": 97,
            "highway_ratio": 0.9,
            "climate_control": "AC on",
            "tire_pressure_note": "Normal",
            "payload_note": "Family trip",
            "notes": "Sample row with actual energy entered"
        },
        {
            "vehicle_id": "vf9",
            "trip_date": "2026-07-11",
            "origin": "Pickering, ON",
            "destination": "Windsor, ON",
            "distance_km": 396.3,
            "starting_soc": 100,
            "ending_soc": 25,
            "charged_energy_kwh": 0,
            "actual_energy_used_kwh": "",
            "predicted_efficiency_kwh_per_100km": 31.7,
            "predicted_energy_used_kwh": 125.6,
            "outside_temperature_c": 24,
            "average_speed_kmh": 96,
            "highway_ratio": 0.9,
            "climate_control": "AC on",
            "tire_pressure_note": "Normal",
            "payload_note": "No actual energy entered",
            "notes": "Sample row where actual energy is calculated from SOC"
        }
    ]

    @staticmethod
    def build_template():
        output = io.StringIO()

        writer = csv.DictWriter(
            output,
            fieldnames=CsvTemplateService.HEADERS
        )

        writer.writeheader()

        for row in CsvTemplateService.SAMPLE_ROWS:
            writer.writerow(
                row
            )

        return output.getvalue()