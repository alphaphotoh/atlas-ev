from backend.services.planning.graph_executor import GraphExecutor


class TripExpander:

    @staticmethod
    async def expand(
        trip
    ):

        return await GraphExecutor.execute(
            trip
        )