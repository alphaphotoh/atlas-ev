class SearchWindowService:

    #
    # Search this many km BEFORE reaching the
    # minimum charger arrival SOC.
    #
    LOOKBEHIND_KM = 50

    #
    # Search this many km AFTER reaching the
    # minimum charger arrival SOC.
    #
    LOOKAHEAD_KM = 100

    SEARCH_SPACING_KM = 20

    @staticmethod
    def build(route, battery_state):

        start_segment = battery_state.segment_index

        while (
            start_segment > 0
            and
            route.segments[start_segment].cumulative_distance_km >
            battery_state.distance_km -
            SearchWindowService.LOOKBEHIND_KM
        ):

            start_segment -= 1

        end_segment = battery_state.segment_index

        while (
            end_segment < len(route.segments) - 1
            and
            route.segments[end_segment].cumulative_distance_km <
            battery_state.distance_km +
            SearchWindowService.LOOKAHEAD_KM
        ):

            end_segment += 1

        return {

            "start_segment": start_segment,

            "end_segment": end_segment,

            "start_distance": (
                route.segments[start_segment]
                .cumulative_distance_km
            ),

            "end_distance": (
                route.segments[end_segment]
                .cumulative_distance_km
            )

        }

    @staticmethod
    def search_points(route, window):

        search_points = []

        next_distance = window["start_distance"]

        for segment in route.segments[
            window["start_segment"]:
            window["end_segment"] + 1
        ]:

            if (
                segment.cumulative_distance_km >=
                next_distance
            ):

                search_points.append({

                    "segment_index": segment.index,

                    "coordinate": segment.center_coordinate,

                    "distance_km": (
                        segment.cumulative_distance_km
                    )

                })

                next_distance += (
                    SearchWindowService
                    .SEARCH_SPACING_KM
                )

        return search_points