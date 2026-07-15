import type {
  PredictionImpact,
  TripSummary as TripSummaryType,
  WaypointMode
} from "../types/trip";

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

function formatKwh(value?: number | null) {
  if (value === null || value === undefined) {
    return "—";
  }

  return `${value.toFixed(1)} kWh`;
}

function formatSignedKwh(value?: number | null) {
  if (value === null || value === undefined) {
    return "—";
  }

  const prefix = value > 0 ? "+" : "";

  return `${prefix}${value.toFixed(1)} kWh`;
}

function formatSignedPercent(value?: number | null) {
  if (value === null || value === undefined) {
    return "—";
  }

  const prefix = value > 0 ? "+" : "";

  return `${prefix}${value.toFixed(1)}%`;
}

function formatMeters(value?: number | null) {
  if (value === null || value === undefined) {
    return "—";
  }

  return `${value.toFixed(0)} m`;
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

function hasPredictionImpact(impact?: PredictionImpact | null) {
  if (!impact) {
    return false;
  }

  return (
    impact.vehicle_base_energy_kwh !== undefined ||
    impact.temperature_impact_kwh !== undefined ||
    impact.wind_impact_kwh !== undefined ||
    impact.elevation_impact_kwh !== undefined ||
    impact.total_impact_kwh !== undefined
  );
}

function PredictionImpactBreakdown({
  impact
}: {
  impact?: PredictionImpact | null;
}) {
  if (!hasPredictionImpact(impact)) {
    return null;
  }

  return (
    <div className="impact-panel">
      <div className="impact-header">
        <div>
          <h3>Prediction Impact Breakdown</h3>
          <p>
            Shows how the original estimate changed after learning, weather, wind,
            and elevation adjustments.
          </p>
        </div>
      </div>

      <div className="impact-grid">
        <div>
          <span>Original Energy Needed</span>
          <strong>{formatKwh(impact?.vehicle_base_energy_kwh)}</strong>
        </div>

        <div>
          <span>After Learning Energy Needed</span>
          <strong>{formatKwh(impact?.learned_base_energy_kwh)}</strong>
        </div>

        <div>
          <span>Final Adjusted Energy Needed</span>
          <strong>{formatKwh(impact?.final_energy_kwh)}</strong>
        </div>

        <div>
          <span>Total Energy Change</span>
          <strong>{formatSignedKwh(impact?.total_impact_kwh)}</strong>
          <small>{formatSignedPercent(impact?.total_soc_impact_percent)} SOC</small>
        </div>

        <div>
          <span>Learning Adjustment</span>
          <strong>{formatSignedKwh(impact?.learning_impact_kwh)}</strong>
          <small>
            {formatSignedPercent(impact?.learning_soc_impact_percent)} SOC
          </small>
        </div>

        <div>
          <span>Temperature Impact</span>
          <strong>{formatSignedKwh(impact?.temperature_impact_kwh)}</strong>
          <small>
            {formatSignedPercent(impact?.temperature_soc_impact_percent)} SOC
          </small>
        </div>

        <div>
          <span>Wind Impact</span>
          <strong>{formatSignedKwh(impact?.wind_impact_kwh)}</strong>
          <small>{formatSignedPercent(impact?.wind_soc_impact_percent)} SOC</small>
        </div>

        <div>
          <span>Elevation Impact</span>
          <strong>{formatSignedKwh(impact?.elevation_impact_kwh)}</strong>
          <small>
            {formatSignedPercent(impact?.elevation_soc_impact_percent)} SOC
          </small>
        </div>

        <div>
          <span>Elevation Gain</span>
          <strong>{formatMeters(impact?.elevation_gain_m)}</strong>
        </div>

        <div>
          <span>Elevation Loss</span>
          <strong>{formatMeters(impact?.elevation_loss_m)}</strong>
        </div>

        <div>
          <span>Net Elevation Change</span>
          <strong>{formatMeters(impact?.net_elevation_change_m)}</strong>
        </div>

        <div>
          <span>Weather/Wind/Elevation change</span>
          <strong>{formatSignedKwh(impact?.conditions_impact_kwh)}</strong>
          <small>
            {formatSignedPercent(impact?.conditions_soc_impact_percent)} SOC
          </small>
        </div>
      </div>

      {impact?.warnings && impact.warnings.length > 0 && (
        <div className="warnings">
          {impact.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      )}
    </div>
  );
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

      <PredictionImpactBreakdown
        impact={summary.prediction_impact}
      />
    </section>
  );
}