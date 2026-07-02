import math


class PhysicsService:

    AIR_DENSITY = 1.225

    GRAVITY = 9.81

    @staticmethod
    def aerodynamic_drag(
        speed_kmh,
        cd=0.31,
        frontal_area=2.9
    ):

        speed = speed_kmh / 3.6

        return (
            0.5
            * PhysicsService.AIR_DENSITY
            * cd
            * frontal_area
            * speed ** 2
        )

    @staticmethod
    def rolling_resistance(
        mass_kg,
        coefficient=0.011
    ):

        return (
            coefficient
            * mass_kg
            * PhysicsService.GRAVITY
        )

    @staticmethod
    def climbing_force(
        mass_kg,
        road_grade_percent
    ):

        return (
            mass_kg
            * PhysicsService.GRAVITY
            * (road_grade_percent / 100)
        )