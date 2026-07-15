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

export interface PredictionImpact {
  vehicle_base_energy_kwh?: number | null;
  learned_base_energy_kwh?: number | null;
  final_energy_kwh?: number | null;

  learning_impact_kwh?: number | null;
  temperature_impact_kwh?: number | null;
  wind_impact_kwh?: number | null;
  elevation_impact_kwh?: number | null;
  conditions_impact_kwh?: number | null;
  total_impact_kwh?: number | null;

  learning_soc_impact_percent?: number | null;
  temperature_soc_impact_percent?: number | null;
  wind_soc_impact_percent?: number | null;
  elevation_soc_impact_percent?: number | null;
  conditions_soc_impact_percent?: number | null;
  total_soc_impact_percent?: number | null;

  elevation_gain_m?: number | null;
  elevation_loss_m?: number | null;
  net_elevation_change_m?: number | null;

  warnings?: string[];
}

export interface SocUncertainty {
  arrival_soc_most_likely_percent?: number | null;
  arrival_soc_low_percent?: number | null;
  arrival_soc_high_percent?: number | null;

  confidence_score?: number | null;

  energy_uncertainty_kwh?: number | null;
  soc_uncertainty_percent?: number | null;
  uncertainty_percent?: number | null;

  factors?: string[];
  warnings?: string[];
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

  predicted_efficiency?: number | null;
  estimated_arrival_soc_without_charging?: number | null;
  actual_arrival_soc_without_charging?: number | null;

  prediction_impact?: PredictionImpact | null;
  soc_uncertainty?: SocUncertainty | null;
}

export interface ChargingStop {
  stop?: number;
  number?: number;
  route_leg?: number;
  planner_leg?: number;

  charger_name?: string;
  name?: string;
  network?: string;
  power_kw?: number | null;

  latitude: number;
  longitude: number;

  route_distance_km?: number | null;
  detour_distance_km?: number | null;
  detour_km?: number | null;
  detour_minutes?: number | null;

  arrival_soc?: number | null;
  departure_soc?: number | null;
  soc_added?: number | null;

  charge_added_kwh?: number | null;
  energy_added_kwh?: number | null;
  charging_time_minutes?: number | null;
  charging_minutes?: number | null;
  charge_time_minutes?: number | null;
  duration_minutes?: number | null;

  destination_soc_if_no_more_charging?: number | null;
  total_minutes_from_this_stop?: number | null;
  score?: number | null;

  reliability_score?: number | null;
  reliability_label?: string | null;
  availability_status?: string | null;
  is_live_availability?: boolean;
  reliability_notes?: string[];

  is_final_stop?: boolean;
}

export interface ChargingPlan {
  stops?: ChargingStop[];
  charging_stops?: ChargingStop[];
}

export interface AlternativePlan {
  plan_id: string;
  route_leg: number;
  label: string;
  is_recommended: boolean;
  stops: number;
  charging_stops: ChargingStop[];
  total_charging_minutes: number;
  total_detour_minutes: number;
  estimated_total_minutes: number;
  final_arrival_soc: number;
  planner_cost: number;
}

export interface AlternativePlansForRouteLeg {
  route_leg: number;
  origin: string;
  destination: string;
  available: boolean;
  recommended_plan_id?: string | null;
  plans: AlternativePlan[];
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
  alternative_plans_by_leg?: AlternativePlansForRouteLeg[] | null;
  map?: TripMapData;
  summary: TripSummary;
}