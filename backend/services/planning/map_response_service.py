class MapResponseService:
    ROUTE_GEOMETRY_FORMAT = "longitude_latitude"

    @staticmethod
    def build(
        origin,
        waypoints,
        destination,
        trips,
        charging_stops
    ):
        route_geometry = MapResponseService.build_route_geometry(
            trips=trips
        )

        markers = MapResponseService.build_markers(
            origin=origin,
            waypoints=waypoints,
            destination=destination,
            trips=trips,
            charging_stops=charging_stops
        )

        bounds = MapResponseService.build_bounds(
            route_geometry=route_geometry,
            markers=markers
        )

        return {
            "route_geometry_format": MapResponseService.ROUTE_GEOMETRY_FORMAT,
            "route_geometry": route_geometry,
            "markers": markers,
            "bounds": bounds
        }

    @staticmethod
    def build_route_geometry(trips):
        route_geometry = []

        for trip in trips:
            route = getattr(
                trip,
                "route",
                None
            )

            geometry = getattr(
                route,
                "geometry",
                None
            )

            if not geometry:
                continue

            for coordinate in geometry:
                serialized = MapResponseService.serialize_coordinate(
                    coordinate
                )

                if serialized is None:
                    continue

                if route_geometry and serialized == route_geometry[-1]:
                    continue

                route_geometry.append(
                    serialized
                )

        return route_geometry

    @staticmethod
    def build_markers(
        origin,
        waypoints,
        destination,
        trips,
        charging_stops
    ):
        markers = []

        origin_coordinate = MapResponseService.first_trip_start_coordinate(
            trips
        )

        if origin_coordinate is not None:
            markers.append(
                MapResponseService.build_location_marker(
                    marker_type="origin",
                    label=origin,
                    coordinate=origin_coordinate
                )
            )

        waypoint_markers = MapResponseService.build_waypoint_markers(
            waypoints=waypoints,
            trips=trips
        )

        markers.extend(
            waypoint_markers
        )

        charger_markers = MapResponseService.build_charger_markers(
            charging_stops=charging_stops
        )

        markers.extend(
            charger_markers
        )

        destination_coordinate = MapResponseService.last_trip_end_coordinate(
            trips
        )

        if destination_coordinate is not None:
            markers.append(
                MapResponseService.build_location_marker(
                    marker_type="destination",
                    label=destination,
                    coordinate=destination_coordinate
                )
            )

        return markers

    @staticmethod
    def build_waypoint_markers(
        waypoints,
        trips
    ):
        markers = []

        if not waypoints:
            return markers

        for index, waypoint in enumerate(waypoints):
            if index >= len(trips):
                continue

            coordinate = MapResponseService.trip_end_coordinate(
                trips[index]
            )

            if coordinate is None:
                continue

            marker = MapResponseService.build_location_marker(
                marker_type="waypoint",
                label=waypoint,
                coordinate=coordinate
            )

            marker["route_leg"] = index + 1

            markers.append(
                marker
            )

        return markers

    @staticmethod
    def build_charger_markers(charging_stops):
        markers = []

        for stop in charging_stops:
            latitude = stop.get(
                "latitude"
            )

            longitude = stop.get(
                "longitude"
            )

            if latitude is None or longitude is None:
                continue

            stop_number = stop.get(
                "stop"
            )

            charger_name = stop.get(
                "charger_name",
                "Charger"
            )

            markers.append(
                {
                    "type": "charger",
                    "label": f"Stop {stop_number}: {charger_name}",
                    "latitude": MapResponseService.round_coordinate_value(
                        latitude
                    ),
                    "longitude": MapResponseService.round_coordinate_value(
                        longitude
                    ),
                    "stop": stop_number,
                    "route_leg": stop.get(
                        "route_leg"
                    ),
                    "charger_name": charger_name,
                    "network": stop.get(
                        "network"
                    ),
                    "power_kw": stop.get(
                        "power_kw"
                    )
                }
            )

        return markers

    @staticmethod
    def build_location_marker(
        marker_type,
        label,
        coordinate
    ):
        longitude = coordinate[0]
        latitude = coordinate[1]

        return {
            "type": marker_type,
            "label": label,
            "latitude": MapResponseService.round_coordinate_value(
                latitude
            ),
            "longitude": MapResponseService.round_coordinate_value(
                longitude
            )
        }

    @staticmethod
    def build_bounds(
        route_geometry,
        markers
    ):
        latitudes = []
        longitudes = []

        for coordinate in route_geometry:
            if len(coordinate) < 2:
                continue

            longitudes.append(
                coordinate[0]
            )

            latitudes.append(
                coordinate[1]
            )

        for marker in markers:
            latitude = marker.get(
                "latitude"
            )

            longitude = marker.get(
                "longitude"
            )

            if latitude is None or longitude is None:
                continue

            latitudes.append(
                latitude
            )

            longitudes.append(
                longitude
            )

        if not latitudes or not longitudes:
            return None

        return {
            "min_latitude": min(latitudes),
            "max_latitude": max(latitudes),
            "min_longitude": min(longitudes),
            "max_longitude": max(longitudes)
        }

    @staticmethod
    def first_trip_start_coordinate(trips):
        if not trips:
            return None

        return MapResponseService.trip_start_coordinate(
            trips[0]
        )

    @staticmethod
    def last_trip_end_coordinate(trips):
        if not trips:
            return None

        return MapResponseService.trip_end_coordinate(
            trips[-1]
        )

    @staticmethod
    def trip_start_coordinate(trip):
        route = getattr(
            trip,
            "route",
            None
        )

        geometry = getattr(
            route,
            "geometry",
            None
        )

        if not geometry:
            return None

        return MapResponseService.serialize_coordinate(
            geometry[0]
        )

    @staticmethod
    def trip_end_coordinate(trip):
        route = getattr(
            trip,
            "route",
            None
        )

        geometry = getattr(
            route,
            "geometry",
            None
        )

        if not geometry:
            return None

        return MapResponseService.serialize_coordinate(
            geometry[-1]
        )

    @staticmethod
    def serialize_coordinate(coordinate):
        if coordinate is None:
            return None

        if len(coordinate) < 2:
            return None

        longitude = coordinate[0]
        latitude = coordinate[1]

        if longitude is None or latitude is None:
            return None

        return [
            MapResponseService.round_coordinate_value(
                longitude
            ),
            MapResponseService.round_coordinate_value(
                latitude
            )
        ]

    @staticmethod
    def round_coordinate_value(value):
        return round(
            float(value),
            6
        )