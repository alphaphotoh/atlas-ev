class CorridorCache:

    _cache = {}

    @staticmethod
    def get(route):

        key = CorridorCache.key(route)

        return CorridorCache._cache.get(
            key
        )

    @staticmethod
    def set(
        route,
        chargers
    ):

        key = CorridorCache.key(route)

        CorridorCache._cache[key] = (
            chargers
        )

    @staticmethod
    def key(
        route
    ):

        start = route.geometry[0]

        end = route.geometry[-1]

        return (

            round(start[0], 5),

            round(start[1], 5),

            round(end[0], 5),

            round(end[1], 5)

        )