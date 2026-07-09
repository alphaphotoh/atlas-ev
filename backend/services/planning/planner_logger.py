import os


class PlannerLogger:
    TRUE_VALUES = {
        "1",
        "true",
        "yes",
        "on",
        "debug",
    }

    @staticmethod
    def enabled():
        value = os.getenv(
            "ATLAS_EV_DEBUG",
            "0"
        )

        return value.lower() in PlannerLogger.TRUE_VALUES

    @staticmethod
    def log(*values):
        if PlannerLogger.enabled():
            print(*values)