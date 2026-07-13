import { useState } from "react";
import type { TripRequest } from "../types/trip";

interface TripFormProps {
  onSubmit: (request: TripRequest) => void;
  loading: boolean;
}

export function TripForm({
  onSubmit,
  loading
}: TripFormProps) {
  const [origin, setOrigin] = useState("Pickering, ON");
  const [waypointsText, setWaypointsText] = useState(
    "Kingston,ON\ncornwall, ON"
  );
  const [destination, setDestination] = useState("Ottawa, ON");
  const [startingSoc, setStartingSoc] = useState(100);
  const [averageSpeed, setAverageSpeed] = useState(110);
  const [highwayRatio, setHighwayRatio] = useState(0.9);

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
      destination,
      starting_soc: startingSoc,
      average_speed: averageSpeed,
      highway_ratio: highwayRatio
    });
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>Plan VF9 Trip</h2>

      <label>
        Origin
        <input
          value={origin}
          onChange={(event) => setOrigin(event.target.value)}
        />
      </label>

      <label>
        Waypoints
        <textarea
          rows={3}
          value={waypointsText}
          onChange={(event) => setWaypointsText(event.target.value)}
        />
      </label>

      <label>
        Destination
        <input
          value={destination}
          onChange={(event) => setDestination(event.target.value)}
        />
      </label>

      <div className="grid">
        <label>
          Starting SOC %
          <input
            type="number"
            value={startingSoc}
            onChange={(event) => setStartingSoc(Number(event.target.value))}
          />
        </label>

        <label>
          Avg Speed km/h
          <input
            type="number"
            value={averageSpeed}
            onChange={(event) => setAverageSpeed(Number(event.target.value))}
          />
        </label>

        <label>
          Highway Ratio
          <input
            type="number"
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