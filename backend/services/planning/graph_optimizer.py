class GraphOptimizer:

    @staticmethod
    def best(nodes):

        if not nodes:

            return None

        return min(

            nodes,

            key=lambda node: (

                node.itinerary.total_trip_minutes,

                node.depth

            )

        )