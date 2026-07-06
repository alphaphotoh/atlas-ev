class RouteCache:

    _cache = {}

    @staticmethod
    def _key(start, end):

        return (

            round(start[0], 6),
            round(start[1], 6),

            round(end[0], 6),
            round(end[1], 6)

        )

    @staticmethod
    def get(start, end):

        return RouteCache._cache.get(

            RouteCache._key(start, end)

        )

    @staticmethod
    def set(start, end, route):

        RouteCache._cache[

            RouteCache._key(start, end)

        ] = route

    @staticmethod
    def clear():

        RouteCache._cache.clear()