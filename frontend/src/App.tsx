import { useState } from "react";
import axios from "axios";

import { planTrip } from "./api/atlasApi";
import { ChargingStops } from "./components/ChargingStops";
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

function App() {
  const [trip, setTrip] = useState<TripResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handlePlanTrip(request: TripRequest) {
    setLoading(true);
    setError("");
    setTrip(null);

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
    <main className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">Atlas EV</p>
          <h1>VF9 Trip Planner</h1>
          <p>
            Plan realistic EV trips with charging stops, route map, SOC,
            detours, total trip time, and charger details.
          </p>
        </div>

        <div className="hero-badge">
          <span>Vehicle</span>
          <strong>VinFast VF9</strong>
        </div>
      </header>

      <TripForm onSubmit={handlePlanTrip} loading={loading} />

      {loading && (
        <section className="card loading-card">
          <div className="spinner" />
          <div>
            <h2>Planning your trip...</h2>
            <p>
              Finding route, estimating energy, checking chargers, and choosing
              stops.
            </p>
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
          <TripSummary
            summary={trip.summary}
            waypointMode={trip.waypoint_mode}
          />
          <RouteLegs legs={trip.route_legs} />
          <ChargingStops stops={chargingStops}
              summary={trip.summary} />
          <TripMap mapData={trip.map} />
        </>
      )}
    </main>
  );
}

export default App;