import math
from types import SimpleNamespace


class RouteSegmentService:
    EARTH_RADIUS_KM = 6371.0088

    @staticmethod
    def segments_for_route(route):
        existing_segments = getattr(
            route,
            "segments",
            None
        )

        if existing_segments:
            return existing_segments

        return RouteSegmentService.build_from_geometry(
            route
        )

    @staticmethod
    def build_from_geometry(route):
        geometry = getattr(
            route,
            "geometry",
            []
        ) or []

        if len(geometry) < 2:
            return []

        raw_lengths = []

        for index in range(len(geometry) - 1):
            raw_lengths.append(
                RouteSegmentService.distance_between_coordinates(
                    geometry[index],
                    geometry[index + 1]
                )
            )

        raw_total = sum(
            raw_lengths
        )

        route_distance_km = getattr(
            route,
            "distance_km",
            raw_total
        ) or raw_total

        route_duration_minutes = getattr(
            route,
            "duration_minutes",
            0.0
        ) or 0.0

        if raw_total <= 0:
            return RouteSegmentService.build_equal_segments(
                geometry=geometry,
                route_distance_km=route_distance_km,
                route_duration_minutes=route_duration_minutes
            )

        segments = []
        cumulative_distance = 0.0

        for index, raw_length in enumerate(raw_lengths):
            length_km = (
                raw_length /
                raw_total
            ) * route_distance_km

            duration_minutes = 0.0

            if route_duration_minutes > 0:
                duration_minutes = (
                    raw_length /
                    raw_total
                ) * route_duration_minutes

            cumulative_distance += length_km

            center_coordinate = RouteSegmentService.interpolate_coordinate(
                start=geometry[index],
                end=geometry[index + 1],
                fraction=0.5
            )

            segments.append(
                SimpleNamespace(
                    index=index,
                    length_km=length_km,
                    cumulative_distance_km=cumulative_distance,
                    duration_minutes=duration_minutes,
                    center_coordinate=center_coordinate
                )
            )

        return segments

    @staticmethod
    def build_equal_segments(
        geometry,
        route_distance_km,
        route_duration_minutes
    ):
        count = len(geometry) - 1

        if count <= 0:
            return []

        length_km = route_distance_km / count
        duration_minutes = 0.0

        if route_duration_minutes > 0:
            duration_minutes = route_duration_minutes / count

        segments = []
        cumulative_distance = 0.0

        for index in range(count):
            cumulative_distance += length_km

            center_coordinate = RouteSegmentService.interpolate_coordinate(
                start=geometry[index],
                end=geometry[index + 1],
                fraction=0.5
            )

            segments.append(
                SimpleNamespace(
                    index=index,
                    length_km=length_km,
                    cumulative_distance_km=cumulative_distance,
                    duration_minutes=duration_minutes,
                    center_coordinate=center_coordinate
                )
            )

        return segments

    @staticmethod
    def sample_points(
        route,
        spacing_km
    ):
        route_distance_km = getattr(
            route,
            "distance_km",
            0.0
        ) or 0.0

        if route_distance_km <= 0:
            return []

        distances = [0.0]

        current = spacing_km

        while current < route_distance_km:
            distances.append(
                current
            )

            current += spacing_km

        if route_distance_km not in distances:
            distances.append(
                route_distance_km
            )

        points = []

        for distance_km in distances:
            coordinate = RouteSegmentService.coordinate_at_distance(
                route=route,
                distance_km=distance_km
            )

            if coordinate is None:
                continue

            points.append(
                {
                    "distance_km": distance_km,
                    "longitude": coordinate[0],
                    "latitude": coordinate[1]
                }
            )

        return points

    @staticmethod
    def coordinate_at_distance(
        route,
        distance_km
    ):
        geometry = getattr(
            route,
            "geometry",
            []
        ) or []

        route_distance_km = getattr(
            route,
            "distance_km",
            0.0
        ) or 0.0

        if len(geometry) >= 2 and route_distance_km > 0:
            return RouteSegmentService.coordinate_from_geometry_distance(
                geometry=geometry,
                target_distance_km=distance_km,
                route_distance_km=route_distance_km
            )

        segments = RouteSegmentService.segments_for_route(
            route
        )

        if not segments:
            return None

        closest = min(
            segments,
            key=lambda segment: abs(
                segment.cumulative_distance_km -
                distance_km
            )
        )

        return closest.center_coordinate

    @staticmethod
    def coordinate_from_geometry_distance(
        geometry,
        target_distance_km,
        route_distance_km
    ):
        if target_distance_km <= 0:
            return geometry[0]

        if target_distance_km >= route_distance_km:
            return geometry[-1]

        raw_lengths = []

        for index in range(len(geometry) - 1):
            raw_lengths.append(
                RouteSegmentService.distance_between_coordinates(
                    geometry[index],
                    geometry[index + 1]
                )
            )

        raw_total = sum(
            raw_lengths
        )

        if raw_total <= 0:
            return geometry[0]

        target_raw_distance = (
            target_distance_km /
            route_distance_km
        ) * raw_total

        travelled = 0.0

        for index, raw_length in enumerate(raw_lengths):
            next_travelled = travelled + raw_length

            if target_raw_distance <= next_travelled:
                if raw_length <= 0:
                    return geometry[index]

                fraction = (
                    target_raw_distance -
                    travelled
                ) / raw_length

                return RouteSegmentService.interpolate_coordinate(
                    start=geometry[index],
                    end=geometry[index + 1],
                    fraction=fraction
                )

            travelled = next_travelled

        return geometry[-1]

    @staticmethod
    def interpolate_coordinate(
        start,
        end,
        fraction
    ):
        return [
            start[0] + ((end[0] - start[0]) * fraction),
            start[1] + ((end[1] - start[1]) * fraction)
        ]

    @staticmethod
    def distance_between_coordinates(
        first,
        second
    ):
        lon1 = math.radians(
            first[0]
        )

        lat1 = math.radians(
            first[1]
        )

        lon2 = math.radians(
            second[0]
        )

        lat2 = math.radians(
            second[1]
        )

        delta_lon = lon2 - lon1
        delta_lat = lat2 - lat1

        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1) *
            math.cos(lat2) *
            math.sin(delta_lon / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        return RouteSegmentService.EARTH_RADIUS_KM * c