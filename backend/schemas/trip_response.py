from pydantic import BaseModel


class WeatherResponse(BaseModel):
    temperature_c: float
    wind_speed_kph: float
    wind_direction_degrees: float
    humidity_percent: float
    pressure_hpa: float
    precipitation_mm: float
    snowfall_cm: float


class RouteWeatherSampleResponse(BaseModel):
    distance_km: float
    temperature_c: float
    wind_speed_kph: float
    wind_direction_degrees: float
    precipitation_mm: float
    snowfall_cm: float
    elevation_m: float | None = None
    grade_percent: float


class EfficiencyProfileSampleResponse(BaseModel):
    distance_km: float
    efficiency: float


class RouteLegResponse(BaseModel):
    leg: int
    origin: str
    destination: str
    distance_km: float
    duration_minutes: int
    energy_kwh: float
    arrival_soc_without_charging: float
    arrival_soc_with_charging: float
    charging_required: bool
    charging_stop_numbers: list[int]


class ChargingStopResponse(BaseModel):
    stop: int
    route_leg: int
    planner_leg: int

    charger_name: str
    network: str | None = None
    power_kw: float | None = None

    latitude: float | None = None
    longitude: float | None = None

    route_distance_km: float
    detour_km: float
    detour_minutes: float

    arrival_soc: float
    departure_soc: float
    soc_added: float

    charge_added_kwh: float
    charging_minutes: float

    destination_soc_if_no_more_charging: float
    total_minutes_from_this_stop: float
    score: float

    is_final_stop: bool


class ChargingPlanResponse(BaseModel):
    charging_required: bool
    stops: int
    charging_stops: list[ChargingStopResponse]
    total_charging_minutes: float
    total_detour_minutes: float


class AlternativePlanResponse(BaseModel):
    plan_id: str
    route_leg: int
    label: str
    is_recommended: bool

    stops: int
    charging_stops: list[ChargingStopResponse]

    total_charging_minutes: float
    total_detour_minutes: float
    estimated_total_minutes: float
    final_arrival_soc: float
    planner_cost: float


class AlternativePlansResponse(BaseModel):
    available: bool
    scope: str
    plans: list[AlternativePlanResponse]


class AlternativePlansForRouteLegResponse(BaseModel):
    route_leg: int
    origin: str
    destination: str
    available: bool
    recommended_plan_id: str | None = None
    plans: list[AlternativePlanResponse]


class LearningSummaryResponse(BaseModel):
    applied: bool
    vehicle_id: str | None = None

    correction_factor: float = 1.0
    confidence_score: float = 0.0
    observation_count: int = 0

    base_predicted_efficiency: float | None = None
    learned_predicted_efficiency: float | None = None

    average_predicted_efficiency_kwh_per_100km: float | None = None
    average_actual_efficiency_kwh_per_100km: float | None = None
    average_prediction_error_percent: float | None = None


class MapMarkerResponse(BaseModel):
    type: str
    label: str

    latitude: float
    longitude: float

    stop: int | None = None
    route_leg: int | None = None

    charger_name: str | None = None
    network: str | None = None
    power_kw: float | None = None


class MapBoundsResponse(BaseModel):
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float


class MapResponse(BaseModel):
    route_geometry_format: str
    route_geometry: list[list[float]]
    markers: list[MapMarkerResponse]
    bounds: MapBoundsResponse | None = None


class TripSummaryResponse(BaseModel):
    distance_km: float

    driving_minutes: int
    charging_minutes: float
    detour_minutes: float
    total_trip_minutes: float

    energy_kwh: float
    final_arrival_soc: float
    charging_required: bool

    predicted_efficiency: float | None = None
    estimated_arrival_soc_without_charging: float | None = None
    actual_arrival_soc_without_charging: float | None = None


class TripResponse(BaseModel):
    vehicle: str
    origin: str
    destination: str
    waypoints: list[str]

    route_legs: list[RouteLegResponse]
    charging_plan: ChargingPlanResponse
    alternative_plans: AlternativePlansResponse
    alternative_plans_by_leg: list[AlternativePlansForRouteLegResponse] | None = None
    learning: LearningSummaryResponse | None = None
    map: MapResponse | None = None
    summary: TripSummaryResponse

    weather: WeatherResponse | None = None
    route_weather: list[RouteWeatherSampleResponse] | None = None
    efficiency_profile: list[EfficiencyProfileSampleResponse] | None = None