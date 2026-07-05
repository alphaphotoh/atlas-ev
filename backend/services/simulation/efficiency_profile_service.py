from backend.models.efficiency_sample import (
    EfficiencySample,
)


class EfficiencyProfileService:

    @staticmethod
    def build(
        route,
        weather_samples,
        base_efficiency
    ):

        profile = []

        for sample in weather_samples:

            efficiency = base_efficiency

            efficiency += (
                max(
                    20 - sample.weather.temperature_c,
                    0
                )
                * 0.15
            )

            profile.append(

                EfficiencySample(

                    distance_km=sample.route_distance_km,

                    efficiency=round(
                        efficiency,
                        2
                    )

                )

            )

        return profile