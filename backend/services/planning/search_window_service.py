class SearchWindowService:

    LOOKAHEAD_KM = 75
    SEARCH_SPACING_KM = 20

    @staticmethod
    def build(route, battery_state):

        start_segment = battery_state.segment_index

        end_segment = start_segment

        while (
            end_segment < len(route.segments) - 1
            and
            route.segments[end_segment].cumulative_distance_km
            <
            battery_state.distance_km +
            SearchWindowService.LOOKAHEAD_KM
        ):

            end_segment += 1

        return {
            "start_segment": start_segment,
            "end_segment": end_segment,
            "start_distance": battery_state.distance_km,
            "end_distance": route.segments[end_segment].cumulative_distance_km
        }

    @staticmethod
    def search_points(route, window):

        search_points = []

        next_distance = window["start_distance"]

        for segment in route.segments[
            window["start_segment"]:
            window["end_segment"] + 1
        ]:

            if segment.cumulative_distance_km >= next_distance:

                search_points.append({
                    "segment_index": segment.index,
                    "coordinate": segment.center_coordinate,
                    "distance_km": segment.cumulative_distance_km
                })

                next_distance += SearchWindowService.SEARCH_SPACING_KM

        return search_points