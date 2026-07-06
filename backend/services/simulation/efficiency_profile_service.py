import math

from backend.models.efficiency_sample import (
    EfficiencySample,
)

from backend.services.simulation.heading_service import (
    HeadingService,
)


class EfficiencyProfileService:

    @staticmethod
    def temperature_adjustment(
        temperature
    ):

        if temperature <= -20:
            return 10.0

        if temperature <= -10:
            return 7.0

        if temperature <= 0:
            return 4.5

        if temperature <= 10:
            return 2.0

        if temperature <= 20:
            return 0.5

        if temperature <= 25:
            return 0.0

        if temperature <= 30:
            return 0.5

        if temperature <= 35:
            return 1.2

        return 2.0

    @staticmethod
    def wind_adjustment(
        wind_speed_kph,
        wind_direction_degrees,
        vehicle_heading
    ):

        difference = abs(

            wind_direction_degrees -

            vehicle_heading

        )

        if difference > 180:

            difference = 360 - difference

        headwind = math.cos(

            math.radians(

                difference

            )

        )

        return (

            headwind *

            wind_speed_kph *

            0.08

        )

    @staticmethod
    def grade_adjustment(
        grade_percent
    ):

        #
        # Approximate VF9 grade model.
        #

        if grade_percent >= 8:
            return 6.0

        if grade_percent >= 6:
            return 4.5

        if grade_percent >= 4:
            return 3.0

        if grade_percent >= 2:
            return 1.5

        if grade_percent <= -8:
            return -4.0

        if grade_percent <= -6:
            return -3.0

        if grade_percent <= -4:
            return -2.0

        if grade_percent <= -2:
            return -1.0

        return grade_percent * 0.5

    @staticmethod
    def build(
        route,
        environment_samples,
        base_efficiency
    ):

        profile = []

        for sample in environment_samples:

            heading = (

                HeadingService.heading_at_distance(

                    route,

                    sample.route_distance_km

                )

            )

            efficiency = base_efficiency

            efficiency += (

                EfficiencyProfileService
                .temperature_adjustment(

                    sample.weather.temperature_c

                )

            )

            efficiency += (

                EfficiencyProfileService
                .wind_adjustment(

                    sample.weather.wind_speed_kph,

                    sample.weather.wind_direction_degrees,

                    heading

                )

            )

            if sample.elevation_m is not None:

                efficiency += (

                    EfficiencyProfileService
                    .grade_adjustment(

                        sample.grade_percent

                    )

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