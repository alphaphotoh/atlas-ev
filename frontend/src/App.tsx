import { useState } from "react";

import { planTrip } from "./api/atlasApi";
import { ChargingStops } from "./components/ChargingStops";
import { TripForm } from "./components/TripForm";
import { TripMap } from "./components/TripMap";
import { TripSummary } from "./components/TripSummary";
import type { TripRequest, TripResponse } from "./types/trip";

import "./App.css";

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
      setError("Trip planning failed. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">Atlas EV</p>
          <h1>VF9 Trip Planner</h1>
          <p>
            Plan realistic EV trips with charging stops, route map, SOC,
            detours, and total trip time.
          </p>
        </div>
      </header>

      <TripForm onSubmit={handlePlanTrip} loading={loading} />

      {error && <div className="error">{error}</div>}

      {trip && (
        <>
          <TripSummary summary={trip.summary} />
          <ChargingStops stops={trip.charging_stops} />
          <TripMap mapData={trip.map} />
        </>
      )}
    </main>
  );
}

export default App;