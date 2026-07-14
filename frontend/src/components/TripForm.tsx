import { useState } from "react";
import type { TripRequest, WaypointMode } from "../types/trip";

interface TripFormProps {
  onSubmit: (request: TripRequest) => void;
  loading: boolean;
}

const sampleTrip = {
  origin: "Pickering, ON",
  waypointsText: "Kingston,ON\ncornwall, ON",
  waypointMode: "via_points" as WaypointMode,
  destination: "Ottawa, ON",
  startingSoc: 100,
  averageSpeed: 110,
  highwayRatio: 0.9
};

export function TripForm({
  onSubmit,
  loading
}: TripFormProps) {
  const [origin, setOrigin] = useState(sampleTrip.origin);
  const [waypointsText, setWaypointsText] = useState(
    sampleTrip.waypointsText
  );
  const [waypointMode, setWaypointMode] = useState<WaypointMode>(
    sampleTrip.waypointMode
  );
  const [destination, setDestination] = useState(sampleTrip.destination);
  const [startingSoc, setStartingSoc] = useState(sampleTrip.startingSoc);
  const [averageSpeed, setAverageSpeed] = useState(sampleTrip.averageSpeed);
  const [highwayRatio, setHighwayRatio] = useState(sampleTrip.highwayRatio);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    const waypoints = waypointsText
      .split("\n")
      .map((value) => value.trim())
      .filter((value) => value.length > 0);

    onSubmit({
      vehicle: "vf9",
      origin,
      waypoints,
      waypoint_mode: waypointMode,
      destination,
      starting_soc: startingSoc,
      average_speed: averageSpeed,
      highway_ratio: highwayRatio
    });
  }

  function resetSampleTrip() {
    setOrigin(sampleTrip.origin);
    setWaypointsText(sampleTrip.waypointsText);
    setWaypointMode(sampleTrip.waypointMode);
    setDestination(sampleTrip.destination);
    setStartingSoc(sampleTrip.startingSoc);
    setAverageSpeed(sampleTrip.averageSpeed);
    setHighwayRatio(sampleTrip.highwayRatio);
  }

  return (
    <form className="card form-card" onSubmit={handleSubmit}>
      <div className="section-header">
        <div>
          <h2>Plan VF9 Trip</h2>
          <p>
            Enter your route, starting battery level, speed, and highway usage.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={resetSampleTrip}
          disabled={loading}
        >
          Reset Sample
        </button>
      </div>

      <div className="route-grid">
        <label>
          Origin
          <input
            value={origin}
            onChange={(event) => setOrigin(event.target.value)}
            placeholder="Pickering, ON"
          />
        </label>

        <label>
          Destination
          <input
            value={destination}
            onChange={(event) => setDestination(event.target.value)}
            placeholder="Ottawa, ON"
          />
        </label>
      </div>

      <label>
        Waypoints
        <textarea
          rows={3}
          value={waypointsText}
          onChange={(event) => setWaypointsText(event.target.value)}
          placeholder={"Kingston,ON\ncornwall, ON"}
        />
        <small>Enter one waypoint per line.</small>
      </label>

      <label>
        Waypoint Mode
        <select
          value={waypointMode}
          onChange={(event) => setWaypointMode(event.target.value as WaypointMode)}
        >
          <option value="via_points">
            Via points only — shape the route, do not force SOC at each waypoint
          </option>
          <option value="required_stops">
            Required stops — treat each waypoint as a separate trip leg
          </option>
        </select>
      </label>

      <div className="grid">
        <label>
          Starting SOC %
          <input
            type="number"
            min={1}
            max={100}
            value={startingSoc}
            onChange={(event) => setStartingSoc(Number(event.target.value))}
          />
        </label>

        <label>
          Avg Speed km/h
          <input
            type="number"
            min={40}
            max={140}
            value={averageSpeed}
            onChange={(event) => setAverageSpeed(Number(event.target.value))}
          />
        </label>

        <label>
          Highway Ratio
          <input
            type="number"
            min={0}
            max={1}
            step="0.1"
            value={highwayRatio}
            onChange={(event) => setHighwayRatio(Number(event.target.value))}
          />
        </label>
      </div>

      <button type="submit" disabled={loading}>
        {loading ? "Planning..." : "Plan Trip"}
      </button>
    </form>
  );
}