import type {
  PredictionImpact,
  TrafficImpact,
  TripConditionsImpact,
  SocUncertainty,
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

function formatPercent(value?: number | null) {
  if (value === null || value === undefined) {
    return "—";
  }

  return `${value.toFixed(1)}%`;
}

function formatSignedPercent(value?: number | null) {
  if (value === null || value === undefined) {
    return "—";
  }

  const prefix = value > 0 ? "+" : "";

  return `${prefix}${value.toFixed(1)}%`;
}

function formatConfidence(value?: number | null) {
  if (value === null || value === undefined) {
    return "—";
  }

  return `${(value * 100).toFixed(0)}%`;
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

function hasSocUncertainty(uncertainty?: SocUncertainty | null) {
  if (!uncertainty) {
    return false;
  }

  return (
    uncertainty.arrival_soc_low_percent !== undefined ||
    uncertainty.arrival_soc_high_percent !== undefined ||
    uncertainty.confidence_score !== undefined
  );
}

function SocUncertaintyPanel({
  uncertainty
}: {
  uncertainty?: SocUncertainty | null;
}) {
  if (!hasSocUncertainty(uncertainty)) {
    return null;
  }

  return (
    <div className="uncertainty-panel">
      <div className="impact-header">
        <div>
          <h3>Final SOC Confidence Range</h3>
          <p>
            Shows a realistic arrival SOC range instead of one exact number.
          </p>
        </div>
      </div>

      <div className="uncertainty-hero">
        <div>
          <span>Expected Final SOC Range</span>
          <strong>
            {formatPercent(uncertainty?.arrival_soc_low_percent)}
            {" – "}
            {formatPercent(uncertainty?.arrival_soc_high_percent)}
          </strong>
        </div>

        <div>
          <span>Most Likely Final SOC</span>
          <strong>
            {formatPercent(uncertainty?.arrival_soc_most_likely_percent)}
          </strong>
        </div>

        <div>
          <span>Confidence</span>
          <strong>{formatConfidence(uncertainty?.confidence_score)}</strong>
        </div>
      </div>

      <div className="impact-grid compact-impact-grid">
        <div>
          <span>Energy Uncertainty</span>
          <strong>{formatKwh(uncertainty?.energy_uncertainty_kwh)}</strong>
        </div>

        <div>
          <span>SOC Uncertainty</span>
          <strong>±{formatPercent(uncertainty?.soc_uncertainty_percent)}</strong>
        </div>

        <div>
          <span>Model Uncertainty</span>
          <strong>{formatPercent(uncertainty?.uncertainty_percent)}</strong>
        </div>
      </div>

      {uncertainty?.factors && uncertainty.factors.length > 0 && (
        <div className="factor-list">
          <span>Uncertainty Factors</span>

          <div>
            {uncertainty.factors.map((factor) => (
              <strong key={factor}>{factor}</strong>
            ))}
          </div>
        </div>
      )}

      {uncertainty?.warnings && uncertainty.warnings.length > 0 && (
        <div className="warnings">
          {uncertainty.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      )}
    </div>
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
            Shows how the original estimate changed after learning, weather,
            wind, and elevation adjustments.
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
          <span>Weather / Wind / Elevation / Trip Conditions Change</span>
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



function TrafficImpactPanel({
  impact
}: {
  impact?: TrafficImpact | null;
}) {
  if (!impact?.applied) {
    return null;
  }

  const factors = impact.factors ?? [];
  const warnings = impact.warnings ?? [];

  const liveTrafficUnavailable =
    impact.mode === "live" &&
    (
      warnings.some((warning) =>
        warning.toLowerCase().includes("fallback") ||
        warning.toLowerCase().includes("unavailable") ||
        warning.toLowerCase().includes("google")
      ) ||
      factors.some((factor) =>
        factor.toLowerCase().includes("fallback") ||
        factor.toLowerCase().includes("estimated traffic") ||
        factor.toLowerCase().includes("live traffic unavailable")
      )
    );

  const liveTrafficConnected =
    impact.mode === "live" && !liveTrafficUnavailable;

  return (
    <section className="impact-panel traffic-impact">
      <div className="impact-header">
        <div>
          <h3>Traffic Impact</h3>
          <p>
            Shows estimated traffic delay and the extra energy needed because
            of stop-and-go or slower driving conditions.
          </p>
        </div>
      </div>

      {liveTrafficUnavailable && (
        <div className="warnings traffic-live-alert">
          <div>
            Live traffic was requested automatically, but Google live traffic was not available for this route.
            Atlas used fallback traffic estimates instead.
          </div>
        </div>
      )}

      {liveTrafficConnected && (
        <div className="mode-note">
          Live traffic connected through Google Routes.
        </div>
      )}

      <div className="impact-grid">
        <div>
          <span>Traffic Mode</span>
          <strong>{impact.mode}</strong>
          <small>{impact.traffic_level}</small>
        </div>

        <div>
          <span>Extra Driving Time</span>
          <strong>{impact.extra_duration_minutes.toFixed(1)} min</strong>
        </div>

        <div>
          <span>Adjusted Driving Time</span>
          <strong>
            {impact.adjusted_duration_minutes !== null &&
            impact.adjusted_duration_minutes !== undefined
              ? `${impact.adjusted_duration_minutes.toFixed(1)} min`
              : "Not available"}
          </strong>
        </div>

        <div>
          <span>Energy Impact</span>
          <strong>{formatKwh(impact.energy_impact_kwh)}</strong>
          <small>
            {impact.soc_impact_percent !== null &&
            impact.soc_impact_percent !== undefined
              ? `${impact.soc_impact_percent.toFixed(1)}% SOC`
              : "SOC impact not available"}
          </small>
        </div>

        <div>
          <span>Efficiency Adjustment</span>
          <strong>
            {impact.efficiency_adjustment_kwh_per_100km.toFixed(2)} kWh/100km
          </strong>
        </div>

        <div>
          <span>Duration Multiplier</span>
          <strong>{impact.duration_multiplier.toFixed(2)}x</strong>
        </div>
      </div>

      {factors.length > 0 && (
        <div className="condition-factor-list">
          <span>Traffic Factors</span>
          <div>
            {factors.map((factor) => (
              <strong key={factor}>{factor}</strong>
            ))}
          </div>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="warning-list">
          {warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      )}
    </section>
  );
}


function TripConditionsImpactPanel({
  impact
}: {
  impact?: TripConditionsImpact | null;
}) {
  if (!impact?.applied) {
    return null;
  }

  const factors = impact.factors ?? [];
  const warnings = impact.warnings ?? [];

  return (
    <section className="impact-panel trip-conditions-impact">
      <div className="impact-header">
        <div>
          <h3>Trip Conditions Impact</h3>
          <p>
            Shows optional condition adjustments from the advanced trip
            conditions section.
          </p>
        </div>
      </div>

      <div className="impact-grid">
        <div>
          <span>Total Condition Energy Impact</span>
          <strong>{formatKwh(impact.energy_impact_kwh)}</strong>
          <small>
            {impact.soc_impact_percent !== null &&
            impact.soc_impact_percent !== undefined
              ? `${impact.soc_impact_percent.toFixed(1)}% SOC`
              : "SOC impact not available"}
          </small>
        </div>

        <div>
          <span>Efficiency Adjustment</span>
          <strong>
            {impact.efficiency_adjustment_kwh_per_100km.toFixed(2)}{" "}
            kWh/100km
          </strong>
        </div>

        <div>
          <span>Passenger/Cargo Impact</span>
          <strong>{formatKwh(impact.passenger_cargo_impact_kwh)}</strong>
        </div>

        <div>
          <span>Climate Impact</span>
          <strong>{formatKwh(impact.climate_impact_kwh)}</strong>
        </div>

        <div>
          <span>Driving Style Impact</span>
          <strong>{formatKwh(impact.driving_style_impact_kwh)}</strong>
        </div>

        <div>
          <span>Road Condition Impact</span>
          <strong>{formatKwh(impact.road_condition_impact_kwh)}</strong>
        </div>

        <div>
          <span>Tire Impact</span>
          <strong>{formatKwh(impact.tire_impact_kwh)}</strong>
        </div>

        <div>
          <span>Roof Load Impact</span>
          <strong>{formatKwh(impact.roof_load_impact_kwh)}</strong>
        </div>

        <div>
          <span>Battery Degradation</span>
          <strong>
            {impact.battery_degradation_percent !== null &&
            impact.battery_degradation_percent !== undefined
              ? `${impact.battery_degradation_percent.toFixed(1)}%`
              : "Not applied"}
          </strong>
        </div>

        <div>
          <span>Usable Battery Reduction</span>
          <strong>
            {impact.usable_battery_reduction_kwh !== null &&
            impact.usable_battery_reduction_kwh !== undefined
              ? formatKwh(impact.usable_battery_reduction_kwh)
              : "Not applied"}
          </strong>
        </div>
      </div>

      {factors.length > 0 && (
        <div className="condition-factor-list">
          <span>Applied Factors</span>
          <div>
            {factors.map((factor) => (
              <strong key={factor}>{factor}</strong>
            ))}
          </div>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="warning-list">
          {warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      )}
    </section>
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

      <SocUncertaintyPanel
        uncertainty={summary.soc_uncertainty}
      />

      <PredictionImpactBreakdown
        impact={summary.prediction_impact}
      />
    
      <TrafficImpactPanel impact={summary.traffic_impact} />
</section>
  );
}