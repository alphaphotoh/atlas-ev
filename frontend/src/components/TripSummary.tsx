import type { TripSummary as TripSummaryType } from "../types/trip";

interface TripSummaryProps {
  summary?: TripSummaryType;
}

export function TripSummary({
  summary
}: TripSummaryProps) {
  if (!summary) {
    return null;
  }

  return (
    <section className="card">
      <h2>Trip Summary</h2>

      <div className="summary-grid">
        <div>
          <span>Distance</span>
          <strong>{summary.distance_km.toFixed(1)} km</strong>
        </div>

        <div>
          <span>Driving</span>
          <strong>{summary.driving_minutes.toFixed(0)} min</strong>
        </div>

        <div>
          <span>Charging</span>
          <strong>{summary.charging_minutes.toFixed(1)} min</strong>
        </div>

        <div>
          <span>Detour</span>
          <strong>{summary.detour_minutes.toFixed(1)} min</strong>
        </div>

        <div>
          <span>Total Time</span>
          <strong>{summary.total_trip_minutes.toFixed(1)} min</strong>
        </div>

        <div>
          <span>Energy</span>
          <strong>{summary.energy_kwh.toFixed(1)} kWh</strong>
        </div>

        <div>
          <span>Final SOC</span>
          <strong>{summary.final_arrival_soc.toFixed(1)}%</strong>
        </div>

        <div>
          <span>Status</span>
          <strong>{summary.planning_status}</strong>
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