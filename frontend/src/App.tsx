import { useState } from "react";
import axios from "axios";

import { planTrip } from "./api/atlasApi";
import { AlternativePlans } from "./components/AlternativePlans";
import { AvailabilityRiskPanel } from "./components/AvailabilityRiskPanel";
import { ChargingStops } from "./components/ChargingStops";
import { GoogleMapsShare } from "./components/GoogleMapsShare";
import { RouteLegs } from "./components/RouteLegs";
import { TripForm } from "./components/TripForm";
import { TripMap } from "./components/TripMap";
import { TripSummary } from "./components/TripSummary";
import type { ChargingStop, TripRequest, TripResponse } from "./types/trip";

import "./App.css";

function getChargingStops(trip: TripResponse): ChargingStop[] {
  if (trip.charging_stops && trip.charging_stops.length > 0) {
    return trip.charging_stops;
  }

  if (trip.charging_plan?.stops && trip.charging_plan.stops.length > 0) {
    return trip.charging_plan.stops;
  }

  if (
    trip.charging_plan?.charging_stops &&
    trip.charging_plan.charging_stops.length > 0
  ) {
    return trip.charging_plan.charging_stops;
  }

  return [];
}

function firstNumber(source: unknown, keys: string[]): number | null {
  if (!source || typeof source !== "object") {
    return null;
  }

  const record = source as Record<string, unknown>;

  for (const key of keys) {
    const value = record[key];

    if (typeof value === "number" && Number.isFinite(value)) {
      return value;
    }

    if (typeof value === "string") {
      const parsed = Number(value);

      if (Number.isFinite(parsed)) {
        return parsed;
      }
    }
  }

  return null;
}

function firstString(source: unknown, keys: string[]): string | null {
  if (!source || typeof source !== "object") {
    return null;
  }

  const record = source as Record<string, unknown>;

  for (const key of keys) {
    const value = record[key];

    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }

    if (typeof value === "number") {
      return String(value);
    }

    if (typeof value === "boolean") {
      return value ? "true" : "false";
    }
  }

  return null;
}

function formatAvailabilityStatus(status: string | null) {
  switch ((status ?? "unknown").toLowerCase()) {
    case "available":
      return "Available";
    case "limited":
      return "Limited";
    case "busy":
      return "Busy";
    case "offline":
      return "Offline";
    case "unknown":
    default:
      return "Availability unknown";
  }
}

function availabilityClass(status: string | null) {
  const normalized = (status ?? "unknown").toLowerCase();

  if (["available", "limited", "busy", "offline"].includes(normalized)) {
    return normalized;
  }

  return "unknown";
}



function getTimelineSocStrategy(stop: unknown): Record<string, unknown> {
  if (!stop || typeof stop !== "object") {
    return {};
  }

  const record = stop as Record<string, unknown>;

  const strategy = record.soc_strategy ?? record.socStrategy;

  if (!strategy || typeof strategy !== "object") {
    return {};
  }

  return strategy as Record<string, unknown>;
}

function formatTimelineSocStrategyLabel(stop: unknown): string {
  const strategy = getTimelineSocStrategy(stop);

  const explicitLabel =
    firstString(strategy, [
      "strategy",
      "label",
      "name",
    ]) ??
    firstString(stop, [
      "soc_strategy_label",
      "socStrategyLabel",
    ]);

  if (explicitLabel) {
    return explicitLabel;
  }

  const selectedTarget =
    firstNumber(strategy, [
      "selected_target_soc",
      "selectedTargetSoc",
      "target_soc",
    ]) ??
    firstNumber(stop, [
      "departure_soc",
      "target_soc",
    ]);

  if (selectedTarget === null) {
    return "SOC strategy inferred";
  }

  const commonTargets = [
    50,
    55,
    60,
    65,
    70,
    75,
    80,
    85,
    90,
    95,
    98,
    100,
  ];

  const nearestCommonTarget = commonTargets.reduce((best, value) =>
    Math.abs(value - selectedTarget) < Math.abs(best - selectedTarget)
      ? value
      : best
  );

  if (selectedTarget >= 99.5) {
    return "Required full charge";
  }

  if (selectedTarget >= 85) {
    return "Upper curve target";
  }

  if (Math.abs(nearestCommonTarget - selectedTarget) <= 0.2) {
    return "Planner target band";
  }

  return "Computed route target";
}



function formatTimelineSocStrategyReason(stop: unknown): string {
  const strategy = getTimelineSocStrategy(stop);

  const explicitReason =
    firstString(strategy, [
      "reason",
      "summary",
    ]) ??
    firstString(stop, [
      "soc_strategy_reason",
      "socStrategyReason",
    ]);

  if (explicitReason) {
    return explicitReason;
  }

  const arrivalSoc = firstNumber(stop, [
    "arrival_soc",
  ]);

  const selectedTarget =
    firstNumber(strategy, [
      "selected_target_soc",
      "selectedTargetSoc",
      "target_soc",
    ]) ??
    firstNumber(stop, [
      "departure_soc",
      "target_soc",
    ]);

  if (selectedTarget === null) {
    return "Atlas selected this departure SOC from the feasible route plan.";
  }

  const commonTargets = [
    50,
    55,
    60,
    65,
    70,
    75,
    80,
    85,
    90,
    95,
    98,
    100,
  ];

  const nearestCommonTarget = commonTargets.reduce((best, value) =>
    Math.abs(value - selectedTarget) < Math.abs(best - selectedTarget)
      ? value
      : best
  );

  const isCommonTarget =
    Math.abs(nearestCommonTarget - selectedTarget) <= 0.2;

  if (selectedTarget >= 99.5) {
    return "The route required a near-full charge to preserve reachability.";
  }

  if (selectedTarget >= 85) {
    return "Atlas selected a high SOC target because the downstream route needed more energy.";
  }

  if (isCommonTarget) {
    return "Atlas selected this feasible target band after considering charging time, reachability, and downstream route needs.";
  }

  if (arrivalSoc !== null) {
    return `Atlas calculated this route-specific target from ${arrivalSoc.toFixed(
      1
    )}% arrival SOC and downstream energy needs.`;
  }

  return "Atlas calculated this route-specific SOC target from the selected charging plan.";
}



function formatTimelineSocTarget(stop: unknown): string {
  const strategy = getTimelineSocStrategy(stop);

  const selectedTarget =
    firstNumber(strategy, [
      "selected_target_soc",
      "selectedTargetSoc",
      "target_soc",
    ]) ??
    firstNumber(stop, [
      "departure_soc",
      "target_soc",
    ]);

  if (selectedTarget === null) {
    return "Target unknown";
  }

  return `${selectedTarget.toFixed(1)}%`;
}

function formatTimelineSocAdded(stop: unknown): string {
  const strategy = getTimelineSocStrategy(stop);

  const socAdded =
    firstNumber(strategy, [
      "soc_added",
      "socAdded",
    ]) ??
    firstNumber(stop, [
      "soc_added",
    ]);

  if (socAdded === null) {
    return "SOC added unknown";
  }

  return `+${socAdded.toFixed(1)}%`;
}

function formatTimelineSocCandidates(stop: unknown): string {
  const strategy = getTimelineSocStrategy(stop);

  const values = strategy.candidate_targets;

  if (Array.isArray(values) && values.length > 0) {
    const formatted = values
      .map((value) => {
        const numericValue = Number(value);

        if (!Number.isFinite(numericValue)) {
          return null;
        }

        return `${numericValue.toFixed(1)}%`;
      })
      .filter(Boolean);

    if (formatted.length > 0) {
      if (formatted.length > 8) {
        return `${formatted.slice(0, 8).join(", ")}...`;
      }

      return formatted.join(", ");
    }
  }

  const arrivalSoc = firstNumber(stop, [
    "arrival_soc",
  ]);

  const selectedTarget =
    firstNumber(strategy, [
      "selected_target_soc",
      "selectedTargetSoc",
      "target_soc",
    ]) ??
    firstNumber(stop, [
      "departure_soc",
      "target_soc",
    ]);

  if (selectedTarget === null) {
    return "Estimated targets unavailable";
  }

  const minimumTarget = Math.max(
    (arrivalSoc ?? 0) + 8,
    35
  );

  const softCap = 85;
  const estimatedTargets: number[] = [];

  let currentTarget = minimumTarget;

  while (currentTarget <= softCap) {
    estimatedTargets.push(
      Number(currentTarget.toFixed(1))
    );

    currentTarget += 5;
  }

  estimatedTargets.push(
    Number(selectedTarget.toFixed(1))
  );

  const uniqueTargets = Array.from(
    new Set(estimatedTargets)
  ).sort((first, second) => first - second);

  const formatted = uniqueTargets.map(
    (value) => `${value.toFixed(1)}%`
  );

  if (formatted.length > 8) {
    return `${formatted.slice(0, 8).join(", ")}...`;
  }

  return formatted.join(", ");
}




function formatTimelineChargerPower(stop: unknown): string {
  const powerKw = firstNumber(stop, [
    "power_kw",
    "max_power_kw",
    "charger_power_kw",
    "maximum_power_kw",
    "dc_power_kw",
  ]);

  if (powerKw === null || powerKw <= 0) {
    return "Power unknown";
  }

  return `${Math.round(powerKw)} kW`;
}

function formatTimelineNetwork(stop: unknown): string {
  return (
    firstString(stop, [
      "network",
      "operator",
      "operator_name",
      "provider",
    ]) ?? "Network unknown"
  );
}

function formatTimelineAvailability(stop: unknown): string {
  const status =
    firstString(stop, [
      "availability_status",
      "availability",
      "status",
    ]) ?? "unknown";

  switch (status.toLowerCase()) {
    case "available":
      return "Available";
    case "limited":
      return "Limited";
    case "busy":
      return "Busy";
    case "offline":
      return "Offline";
    case "unknown":
      return "Availability unknown";
    default:
      return status;
  }
}

function formatTimelineReliability(stop: unknown): string {
  const label =
    firstString(stop, [
      "reliability_label",
      "reliability",
    ]) ?? null;

  const score = firstNumber(stop, [
    "reliability_score",
    "reliabilityScore",
  ]);

  if (label && score !== null) {
    const percent = score <= 1 ? score * 100 : score;

    return `${label} · ${Math.round(percent)}%`;
  }

  if (label) {
    return label;
  }

  if (score !== null) {
    const percent = score <= 1 ? score * 100 : score;

    return `${Math.round(percent)}% reliability`;
  }

  return "Reliability unknown";
}

function formatTimelineQuality(stop: unknown): string {
  const network = formatTimelineNetwork(stop).toLowerCase();
  const powerKw = firstNumber(stop, [
    "power_kw",
    "max_power_kw",
    "charger_power_kw",
    "maximum_power_kw",
    "dc_power_kw",
  ]);

  if (
    network.includes("electrify") ||
    network.includes("tesla") ||
    network.includes("chargepoint") ||
    network.includes("evgo") ||
    network.includes("flo") ||
    network.includes("petro-canada") ||
    network.includes("ivy")
  ) {
    if (powerKw !== null && powerKw >= 150) {
      return "Trusted high-power stop";
    }

    return "Trusted network";
  }

  if (
    network.includes("unknown") ||
    network.includes("(unknown operator)")
  ) {
    if (powerKw !== null && powerKw >= 150) {
      return "High power · unknown operator";
    }

    return "Unknown operator";
  }

  if (powerKw !== null && powerKw >= 150) {
    return "High-power stop";
  }

  if (powerKw !== null && powerKw > 0) {
    return "Standard DC stop";
  }

  return "Quality unknown";
}


function getFinalSoc(summary: unknown): number | null {
  return firstNumber(summary, [
    "final_arrival_soc",
    "final_soc",
    "final_soc_percent",
    "arrival_soc",
    "arrival_soc_percent",
    "estimated_arrival_soc",
    "estimated_arrival_soc_percent",
    "destination_arrival_soc",
    "destination_arrival_soc_percent",
    "ending_soc",
    "ending_soc_percent"
  ]);
}

function getRouteAverageSpeed(summary: unknown): number | null {
  const distanceKm = firstNumber(summary, [
    "distance_km",
    "total_distance_km"
  ]);

  const drivingMinutes = firstNumber(summary, [
    "driving_minutes",
    "driving_time_minutes"
  ]);

  if (
    distanceKm === null ||
    drivingMinutes === null ||
    distanceKm <= 0 ||
    drivingMinutes <= 0
  ) {
    return null;
  }

  return distanceKm / (drivingMinutes / 60);
}

function formatSpeed(value: number | null) {
  if (value === null) {
    return "—";
  }

  return `${value.toFixed(1)} km/h`;
}

function formatMinutes(value?: number | null) {
  if (value === null || value === undefined) {
    return "—";
  }

  const rounded = Math.round(value);

  if (rounded < 60) {
    return `${rounded} min`;
  }

  const hours = Math.floor(rounded / 60);
  const minutes = rounded % 60;

  if (minutes === 0) {
    return `${hours} hr`;
  }

  return `${hours} hr ${minutes} min`;
}

function formatPercent(value?: number | null) {
  if (value === null || value === undefined) {
    return "—";
  }

  return `${value.toFixed(1)}%`;
}

function CompactTripHeader({
  trip,
  chargingStops
}: {
  trip: TripResponse;
  chargingStops: ChargingStop[];
}) {
  return (
    <section className="tesla-trip-card">
      <div className="tesla-route-title">
        <span>{trip.origin}</span>
        <strong>→</strong>
        <span>{trip.destination}</span>
      </div>

      <div className="tesla-metrics-row">
        <div>
          <span>Total time</span>
          <strong>
            {formatMinutes(
              firstNumber(trip.summary, [
                "total_time_minutes",
                "total_trip_minutes"
              ])
            )}
          </strong>
        </div>

        <div>
          <span>Driving</span>
          <strong>
            {formatMinutes(
              firstNumber(trip.summary, [
                "driving_time_minutes",
                "driving_minutes"
              ])
            )}
          </strong>
        </div>

        <div>
          <span>Avg speed</span>
          <strong>{formatSpeed(getRouteAverageSpeed(trip.summary))}</strong>
        </div>

        <div>
          <span>Charging</span>
          <strong>
            {formatMinutes(
              firstNumber(trip.summary, [
                "charging_time_minutes",
                "charging_minutes"
              ])
            )}
          </strong>
        </div>

        <div>
          <span>Final SOC</span>
          <strong>
            {formatPercent(getFinalSoc(trip.summary))}
          </strong>
        </div>
      </div>

      <div className="tesla-charge-count">
        <span>{chargingStops.length}</span>
        <p>
          {chargingStops.length === 1
            ? "charging stop planned"
            : "charging stops planned"}
        </p>
      </div>
    </section>
  );
}

function CompactChargingTimeline({
  trip,
  chargingStops
}: {
  trip: TripResponse;
  chargingStops: ChargingStop[];
}) {
  const finalSoc = firstNumber(trip.summary, [
    "estimated_arrival_soc_percent",
    "estimated_arrival_soc",
    "final_soc_percent",
    "arrival_soc_percent",
    "arrival_soc",
    "final_soc",
                "final_arrival_soc",
    "ending_soc",
    "destination_soc",
    "destination_arrival_soc_percent"
  ]);

  const totalTime = firstNumber(trip.summary, [
    "total_time_minutes",
    "total_trip_minutes"
  ]);

  const distanceKm = firstNumber(trip.summary, [
    "distance_km",
    "total_distance_km"
  ]);

  return (
    <section className="tesla-route-timeline-card">
      <div className="tesla-route-timeline-header">
        <div>
          <h3>Route timeline</h3>
          <p>
            {distanceKm === null ? "Distance unavailable" : `${distanceKm.toFixed(1)} km`}
            {" · "}
            {formatMinutes(totalTime)}
          </p>
        </div>

        <span>
          Arrive {formatPercent(finalSoc)}
        </span>
      </div>

      <div className="tesla-route-timeline">
        <div className="tesla-route-node origin-node">
          <div className="tesla-route-icon">O</div>
          <div>
            <strong>{trip.origin}</strong>
            <span>Start</span>
          </div>
        </div>

        {chargingStops.map((stop, index) => {
          const arriveSoc = firstNumber(stop, [
            "arrival_soc_percent",
            "arrival_soc",
            "charger_arrival_soc_percent"
          ]);

          const leaveSoc = firstNumber(stop, [
            "departure_soc_percent",
            "departure_soc",
            "charger_departure_soc_percent"
          ]);

          const chargeTime = firstNumber(stop, [
            "charging_time_minutes",
            "charge_time_minutes",
            "time_minutes"
          ]);

          const energyAdded = firstNumber(stop, [
            "energy_added_kwh",
            "charge_added_kwh"
          ]);

          const detour = firstNumber(stop, [
            "detour_minutes",
            "estimated_detour_minutes"
          ]);

          const availabilityStatus = firstString(stop, [
            "availability_status"
          ]);

          const isLiveAvailability =
            firstString(stop, ["is_live_availability"]) === "true";

          const availableStalls = firstNumber(stop, ["available_stalls"]);

          const totalStalls = firstNumber(stop, ["total_stalls"]);

          const occupancyPercent = firstNumber(stop, ["occupancy_percent"]);

          const availabilitySource = firstString(stop, [
            "availability_source"
          ]);

          return (
            <div className="tesla-route-node charging-node" key={`${stop.name}-${index}`}>
              <div className="tesla-route-connector" />
              <div className="tesla-route-icon">{index + 1}</div>

              <div className="tesla-route-node-body">
                <strong>{stop.charger_name ?? stop.name ?? "Charging stop"}</strong>

                <span>
                  Charge {formatMinutes(chargeTime)}
                  {" · "}
                  {formatPercent(arriveSoc)} → {formatPercent(leaveSoc)}
                </span>

                <div className="tesla-route-quality-grid">
                  <span>
                    <small>Power</small>
                    <strong>{formatTimelineChargerPower(stop)}</strong>
                  </span>

                  <span>
                    <small>Network</small>
                    <strong>{formatTimelineNetwork(stop)}</strong>
                  </span>

                  <span>
                    <small>Reliability</small>
                    <strong>{formatTimelineReliability(stop)}</strong>
                  </span>

                  <span>
                    <small>Quality</small>
                    <strong>{formatTimelineQuality(stop)}</strong>
                  </span>

                  <span>
                    <small>Availability</small>
                    <strong>{formatTimelineAvailability(stop)}</strong>
                  </span>

                  <span>
                    <small>SOC target</small>
                    <strong>{formatTimelineSocTarget(stop)}</strong>
                  </span>

                  <span>
                    <small>SOC added</small>
                    <strong>{formatTimelineSocAdded(stop)}</strong>
                  </span>
                </div>

                <div className="tesla-route-soc-strategy">
                  <strong>{formatTimelineSocStrategyLabel(stop)}</strong>
                  <span>{formatTimelineSocStrategyReason(stop)}</span>
                  <small>
                    Estimated candidate targets: {formatTimelineSocCandidates(stop)}
                  </small>
                </div>

                <div className="tesla-route-mini-metrics">
                  <small>
                    {energyAdded === null ? "Energy —" : `${energyAdded.toFixed(1)} kWh added`}
                  </small>

                  <small>
                    {detour === null ? "Detour —" : `${detour.toFixed(1)} min detour`}
                  </small>
                </div>

                <div
                  className={`tesla-availability-line ${availabilityClass(
                    availabilityStatus
                  )}`}
                >
                  <span className="tesla-availability-dot" />

                  <strong>{formatAvailabilityStatus(availabilityStatus)}</strong>

                  <small>
                    {isLiveAvailability ? "Live" : "Not live"}
                    {availabilitySource ? ` · ${availabilitySource}` : ""}
                    {availableStalls !== null && totalStalls !== null
                      ? ` · ${availableStalls}/${totalStalls} stalls`
                      : totalStalls !== null
                        ? ` · ${totalStalls} stalls listed`
                        : ""}
                    {occupancyPercent !== null
                      ? ` · ${occupancyPercent.toFixed(0)}% occupied`
                      : ""}
                  </small>
                </div>
              </div>
            </div>
          );
        })}

        <div className="tesla-route-node destination-node">
          <div className="tesla-route-connector" />
          <div className="tesla-route-icon">D</div>
          <div>
            <strong>{trip.destination}</strong>
            <span>Arrive with {formatPercent(finalSoc)}</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function App() {
  const [trip, setTrip] = useState<TripResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showDetails, setShowDetails] = useState(false);

  async function handlePlanTrip(request: TripRequest) {
    setLoading(true);
    setError("");
    setTrip(null);
    setShowDetails(false);

    try {
      const result = await planTrip(request);
      setTrip(result);
    } catch (err) {
      console.error(err);

      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;

        if (typeof detail === "string") {
          setError(detail);
        } else {
          setError(
            "Trip planning failed. Make sure the backend is running and CORS is enabled."
          );
        }
      } else {
        setError("Trip planning failed.");
      }
    } finally {
      setLoading(false);
    }
  }

  const chargingStops = trip ? getChargingStops(trip) : [];

  return (
    <main
      className={
        showDetails
          ? "tesla-planner-app tesla-details-open"
          : "tesla-planner-app tesla-details-closed"
      }
    >
      <header className="tesla-topbar">
        <div>
          <strong>Atlas EV</strong>
          <span>VF9 Trip Planner</span>
        </div>

        <div className="tesla-topbar-status">
          <span>VinFast VF9</span>
          <span>Live traffic</span>
        </div>
      </header>

      <section className="tesla-layout">
        <aside className="tesla-side-panel">
          <TripForm onSubmit={handlePlanTrip} loading={loading} />

          {loading && (
            <section className="tesla-loading">
              <div className="spinner" />
              <div>
                <strong>Planning route</strong>
                <span>Checking route, charging, weather, and traffic.</span>
              </div>
            </section>
          )}

          {error && (
            <section className="error">
              <strong>Trip planning failed</strong>
              <p>{error}</p>
            </section>
          )}

          {trip && (
            <>
              <CompactTripHeader trip={trip} chargingStops={chargingStops} />

              <CompactChargingTimeline trip={trip} chargingStops={chargingStops} />

              <AvailabilityRiskPanel
                chargingStops={chargingStops}
                alternativePlansByLeg={trip.alternative_plans_by_leg}
                variant="compact"
              />

              <button
                className="tesla-details-button"
                type="button"
                onClick={() => setShowDetails(!showDetails)}
              >
                {showDetails ? "Hide trip details below map" : "Show trip details below map"}
              </button>
            </>
          )}
        </aside>

        <section className="tesla-map-area">
          <div className="tesla-map-shell">
            {trip ? (
              <TripMap mapData={trip.map} />
            ) : (
              <div className="tesla-map-placeholder">
                <div>
                  <h2>Plan your EV route</h2>
                  <p>
                    Enter a destination to see route, charging stops, SOC, and
                    live traffic impact.
                  </p>
                </div>
              </div>
            )}
          </div>

          {trip && showDetails && (
            <div className="tesla-details-under-map">
              <TripSummary
                summary={trip.summary}
                waypointMode={trip.waypoint_mode}
              />

              <AvailabilityRiskPanel
                chargingStops={chargingStops}
                alternativePlansByLeg={trip.alternative_plans_by_leg}
                variant="full"
              />

              <GoogleMapsShare trip={trip} chargingStops={chargingStops} />

              <RouteLegs legs={trip.route_legs} />

              <ChargingStops
                stops={chargingStops}
                summary={trip.summary}
                alternativePlansByLeg={trip.alternative_plans_by_leg}
              />

              <AlternativePlans
                alternativePlansByLeg={trip.alternative_plans_by_leg}
              />
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default App;