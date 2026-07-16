import { useState } from "react";
import axios from "axios";

import { planTrip } from "./api/atlasApi";
import { AlternativePlans } from "./components/AlternativePlans";
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
            {formatPercent(
              firstNumber(trip.summary, [
                "estimated_arrival_soc_percent",
                "estimated_arrival_soc",
                "final_soc_percent",
                "arrival_soc_percent"
              ])
            )}
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
  chargingStops
}: {
  chargingStops: ChargingStop[];
}) {
  if (chargingStops.length === 0) {
    return (
      <section className="tesla-timeline-card">
        <h3>Charging</h3>
        <p className="tesla-muted">No charging stop required for this trip.</p>
      </section>
    );
  }

  return (
    <section className="tesla-timeline-card">
      <h3>Charging stops</h3>

      <div className="tesla-timeline">
        {chargingStops.map((stop, index) => (
          <div className="tesla-timeline-item" key={`${stop.name}-${index}`}>
            <div className="tesla-timeline-dot">{index + 1}</div>

            <div>
              <strong>{stop.charger_name ?? stop.name ?? "Charging stop"}</strong>
              <span>
                {formatMinutes(
                  firstNumber(stop, [
                    "charging_time_minutes",
                    "charge_time_minutes",
                    "time_minutes"
                  ])
                )}
                {" · "}
                {formatPercent(
                  firstNumber(stop, [
                    "arrival_soc_percent",
                    "arrival_soc",
                    "charger_arrival_soc_percent"
                  ])
                )}{" "}
                →{" "}
                {formatPercent(
                  firstNumber(stop, [
                    "departure_soc_percent",
                    "departure_soc",
                    "charger_departure_soc_percent"
                  ])
                )}
              </span>
            </div>
          </div>
        ))}
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

              <CompactChargingTimeline chargingStops={chargingStops} />

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