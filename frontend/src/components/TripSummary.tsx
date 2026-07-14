import type { TripSummary as TripSummaryType, WaypointMode } from "../types/trip";

interface TripSummaryProps {
  summary?: TripSummaryType;
  waypointMode?: WaypointMode;
}

function formatHours(minutes: number) {
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);

  if (hours <= 0) {
    return `${mins} min`;
  }

  return `${hours} hr ${mins} min`;
}

function waypointModeLabel(waypointMode?: WaypointMode) {
  if (waypointMode === "via_points") {
    return "Via points only";
  }

  if (waypointMode === "required_stops") {
    return "Required stops";
  }

  return "Not specified";
}

function waypointModeDescription(waypointMode?: WaypointMode) {
  if (waypointMode === "via_points") {
    return "Waypoints shape the route but do not force SOC targets.";
  }

  if (waypointMode === "required_stops") {
    return "Waypoints are treated as separate trip legs.";
  }

  return "Waypoint mode was not returned by the backend.";
}

export function TripSummary({
  summary,
  waypointMode
}: TripSummaryProps) {
  if (!summary) {
    return null;
  }

  return (
    <section className="card">
      <div className="section-header">
        <div>
          <h2>Trip Summary</h2>
          <p>
            Status: <strong>{summary.planning_status}</strong>
          </p>
        </div>

        <div className="summary-badges">
          <div className="mode-pill">
            {waypointModeLabel(waypointMode)}
          </div>

          <div className="status-pill">
            {summary.charging_required ? "Charging planned" : "No charge needed"}
          </div>
        </div>
      </div>

      <div className="mode-note">
        {waypointModeDescription(waypointMode)}
      </div>

      <div className="summary-grid">
        <div>
          <span>Distance</span>
          <strong>{summary.distance_km.toFixed(1)} km</strong>
        </div>

        <div>
          <span>Total Time</span>
          <strong>{formatHours(summary.total_trip_minutes)}</strong>
        </div>

        <div>
          <span>Driving</span>
          <strong>{formatHours(summary.driving_minutes)}</strong>
        </div>

        <div>
          <span>Charging</span>
          <strong>{formatHours(summary.charging_minutes)}</strong>
        </div>

        <div>
          <span>Detour</span>
          <strong>{summary.detour_minutes.toFixed(1)} min</strong>
        </div>

        <div>
          <span>Energy Used</span>
          <strong>{summary.energy_kwh.toFixed(1)} kWh</strong>
        </div>

        <div>
          <span>Final SOC</span>
          <strong>{summary.final_arrival_soc.toFixed(1)}%</strong>
        </div>

        <div>
          <span>Warnings</span>
          <strong>{summary.warnings.length}</strong>
        </div>
      </div>

      {summary.warnings.length > 0 && (
        <div className="warnings">
          {summary.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      )}
    </section>
  );
}