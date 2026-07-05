class GraphOptimizer:

    @staticmethod
    def priority(
        node
    ):

        return (

            node.g_cost,

            node.depth

        )

    @staticmethod
    def best(
        nodes
    ):

        if not nodes:

            return None

        nodes.sort(

            key=lambda node: (

                node.itinerary.total_trip_minutes,

                node.itinerary.total_charging_minutes,

                node.itinerary.total_detour_minutes,

                node.depth

            )

        )

        return nodes[0]