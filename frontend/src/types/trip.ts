export type WaypointMode = "required_stops" | "via_points";

export interface TripRequest {
  vehicle: string;
  origin: string;
  waypoints: string[];
  waypoint_mode: WaypointMode;
  destination: string;
  starting_soc: number;
  average_speed: number;
  highway_ratio: number;
}

export interface RouteLeg {
  leg: number;
  origin: string;
  destination: string;
  distance_km: number;
  duration_minutes: number;
  energy_kwh: number;
  arrival_soc_without_charging: number;
  arrival_soc_with_charging: number;
  charging_required: boolean;
  planning_status: string;
  warnings: string[];
  charging_stop_numbers: number[];
}

export interface MapMarker {
  type: string;
  label: string;
  latitude: number;
  longitude: number;
  stop?: number;
  route_leg?: number;
  charger_name?: string;
  network?: string;
  power_kw?: number;
}

export interface MapBounds {
  min_latitude: number;
  max_latitude: number;
  min_longitude: number;
  max_longitude: number;
}

export interface TripMapData {
  route_geometry_format: string;
  route_geometry: number[][];
  markers: MapMarker[];
  bounds?: MapBounds;
}

export interface TripSummary {
  distance_km: number;
  driving_minutes: number;
  charging_minutes: number;
  detour_minutes: number;
  total_trip_minutes: number;
  energy_kwh: number;
  final_arrival_soc: number;
  charging_required: boolean;
  planning_status: string;
  warnings: string[];
}

export interface ChargingStop {
  stop?: number;
  number?: number;
  route_leg?: number;

  charger_name?: string;
  name?: string;
  network?: string;

  latitude: number;
  longitude: number;

  arrival_soc?: number;
  departure_soc?: number;

  charge_added_kwh?: number;
  energy_added_kwh?: number;

  charging_time_minutes?: number;
  charging_minutes?: number;
  charge_time_minutes?: number;
  duration_minutes?: number;

  power_kw?: number;

  detour_distance_km?: number;
  detour_km?: number;
}

export interface ChargingPlan {
  stops?: ChargingStop[];
  charging_stops?: ChargingStop[];
}

export interface TripResponse {
  vehicle: string;
  origin: string;
  destination: string;
  waypoints?: string[];
  waypoint_mode?: WaypointMode;
  route_legs?: RouteLeg[];
  charging_stops?: ChargingStop[];
  charging_plan?: ChargingPlan;
  map?: TripMapData;
  summary: TripSummary;
}