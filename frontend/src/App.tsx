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