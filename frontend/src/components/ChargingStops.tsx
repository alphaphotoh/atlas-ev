import type {
  AlternativePlansForRouteLeg,
  ChargingStop,
  TripSummary
} from "../types/trip";

interface ChargingStopsProps {
  stops: ChargingStop[];
  summary?: TripSummary;
  alternativePlansByLeg?: AlternativePlansForRouteLeg[] | null;
}

function getStopNumber(stop: ChargingStop, index: number) {
  return stop.stop ?? stop.number ?? index + 1;
}

function getChargerName(stop: ChargingStop) {
  return stop.charger_name ?? stop.name ?? "Unknown charger";
}

function getEnergyAdded(stop: ChargingStop) {
  return stop.charge_added_kwh ?? stop.energy_added_kwh ?? 0;
}

function getChargingMinutes(stop: ChargingStop) {
  return (
    stop.charging_minutes ??
    stop.charging_time_minutes ??
    stop.charge_time_minutes ??
    stop.duration_minutes ??
    0
  );
}

function getDetourKm(stop: ChargingStop) {
  return stop.detour_km ?? stop.detour_distance_km ?? 0;
}

function formatNumber(value?: number | null, digits = 1) {
  if (value === null || value === undefined) {
    return "—";
  }

  return value.toFixed(digits);
}

function formatSoc(value?: number | null) {
  if (value === null || value === undefined) {
    return "—";
  }

  return `${value.toFixed(1)}%`;
}

function formatPower(value?: number | null) {
  if (value === null || value === undefined) {
    return "Power unknown";
  }

  return `${value.toFixed(0)} kW`;
}

function finalSocRangeText(summary?: TripSummary) {
  const low = summary?.soc_uncertainty?.arrival_soc_low_percent;
  const high = summary?.soc_uncertainty?.arrival_soc_high_percent;

  if (low === null || low === undefined) {
    return null;
  }

  if (high === null || high === undefined) {
    return null;
  }

  return `${low.toFixed(1)}%–${high.toFixed(1)}%`;
}

function confidenceText(summary?: TripSummary) {
  const confidence = summary?.soc_uncertainty?.confidence_score;

  if (confidence === null || confidence === undefined) {
    return null;
  }

  return `${(confidence * 100).toFixed(0)}%`;
}

function chargerSignature(stop: ChargingStop) {
  return [
    getChargerName(stop).toLowerCase(),
    stop.latitude?.toFixed(4),
    stop.longitude?.toFixed(4)
  ].join("|");
}

function findBackupCharger(
  stop: ChargingStop,
  alternativePlansByLeg?: AlternativePlansForRouteLeg[] | null
) {
  const routeLeg = stop.route_leg;

  if (!routeLeg || !alternativePlansByLeg) {
    return null;
  }

  const group = alternativePlansByLeg.find(
    (item) => item.route_leg === routeLeg
  );

  if (!group || !group.plans) {
    return null;
  }

  const currentSignature = chargerSignature(stop);

  for (const plan of group.plans) {
    if (plan.is_recommended) {
      continue;
    }

    for (const candidate of plan.charging_stops ?? []) {
      if (chargerSignature(candidate) !== currentSignature) {
        return {
          stop: candidate,
          planLabel: plan.label,
          estimatedTotalMinutes: plan.estimated_total_minutes,
          finalArrivalSoc: plan.final_arrival_soc
        };
      }
    }
  }

  return null;
}

function reliabilityClass(label?: string | null) {
  if (label === "High") {
    return "reliability-high";
  }

  if (label === "Medium") {
    return "reliability-medium";
  }

  if (label === "Low") {
    return "reliability-low";
  }

  return "reliability-unknown";
}

function ReliabilityPanel({
  stop,
  backup
}: {
  stop: ChargingStop;
  backup: ReturnType<typeof findBackupCharger>;
}) {
  const label = stop.reliability_label ?? "Unknown";
  const score = stop.reliability_score;
  const availability = stop.availability_status ?? "unknown";
  const liveStatus = stop.is_live_availability
    ? "Live availability connected"
    : "Live availability not connected yet";

  return (
    <div className="reliability-panel">
      <div className="reliability-header">
        <div>
          <h4>Reliability & Backup</h4>
          <p>
            Current MVP score uses network, charger power, and route detour.
          </p>
        </div>

        <div className={`reliability-pill ${reliabilityClass(label)}`}>
          {label}
          {score !== null && score !== undefined ? ` · ${score.toFixed(1)}%` : ""}
        </div>
      </div>

      <div className="reliability-grid">
        <div>
          <span>Availability</span>
          <strong>{availability}</strong>
          <small>{liveStatus}</small>
        </div>

        <div>
          <span>Backup Charger</span>
          {backup ? (
            <>
              <strong>{getChargerName(backup.stop)}</strong>
              <small>
                {backup.stop.network ?? "Network unknown"} ·{" "}
                {formatPower(backup.stop.power_kw)}
              </small>
            </>
          ) : (
            <>
              <strong>No backup shown</strong>
              <small>No different alternative charger found for this leg.</small>
            </>
          )}
        </div>

        {backup && (
          <div>
            <span>Backup Plan</span>
            <strong>{backup.planLabel}</strong>
            <small>
              Est. total {formatNumber(backup.estimatedTotalMinutes, 1)} min ·
              final SOC {formatSoc(backup.finalArrivalSoc)}
            </small>
          </div>
        )}
      </div>

      {stop.reliability_notes && stop.reliability_notes.length > 0 && (
        <div className="reliability-notes">
          {stop.reliability_notes.map((note) => (
            <p key={note}>{note}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function ChargingDecisionExplanation({
  stop,
  summary
}: {
  stop: ChargingStop;
  summary?: TripSummary;
}) {
  const chargerName = getChargerName(stop);
  const chargingMinutes = getChargingMinutes(stop);
  const energyAdded = getEnergyAdded(stop);
  const detourKm = getDetourKm(stop);
  const finalRange = finalSocRangeText(summary);
  const confidence = confidenceText(summary);

  const departureSoc = stop.departure_soc;
  const arrivalSoc = stop.arrival_soc;
  const powerKw = stop.power_kw;

  return (
    <div className="charging-explanation">
      <h4>Why this charging stop?</h4>

      <div className="explanation-grid">
        <div>
          <span>Route fit</span>
          <p>
            {chargerName} was selected because it is close to the planned route
            with an estimated detour of {formatNumber(detourKm, 1)} km.
          </p>
        </div>

        <div>
          <span>Charging speed</span>
          <p>
            This stop offers {formatPower(powerKw)} charging power, helping keep
            charging time to about {formatNumber(chargingMinutes, 1)} minutes.
          </p>
        </div>

        <div>
          <span>Charge target</span>
          <p>
            Atlas plans to charge from {formatSoc(arrivalSoc)} to{" "}
            {formatSoc(departureSoc)}, adding about{" "}
            {formatNumber(energyAdded, 1)} kWh instead of automatically
            charging to 80% or 100%.
          </p>
        </div>

        <div>
          <span>Trip confidence</span>
          <p>
            Expected final SOC is {formatSoc(summary?.final_arrival_soc)}
            {finalRange ? `, with a confidence range of ${finalRange}` : ""}.
            {confidence ? ` Confidence: ${confidence}.` : ""}
          </p>
        </div>
      </div>
    </div>
  );
}

export function ChargingStops({
  stops,
  summary,
  alternativePlansByLeg
}: ChargingStopsProps) {
  if (!stops || stops.length === 0) {
    return (
      <section className="card">
        <h2>Charging Stops</h2>
        <p className="muted">No charging stop needed for this trip.</p>
      </section>
    );
  }

  return (
    <section className="card">
      <h2>Charging Stops</h2>
      <p className="muted">
        {stops.length} planned {stops.length === 1 ? "stop" : "stops"}
      </p>

      <div className="stop-list">
        {stops.map((stop, index) => {
          const stopNumber = getStopNumber(stop, index);
          const chargerName = getChargerName(stop);
          const chargingMinutes = getChargingMinutes(stop);
          const energyAdded = getEnergyAdded(stop);
          const detourKm = getDetourKm(stop);
          const backup = findBackupCharger(
            stop,
            alternativePlansByLeg
          );

          return (
            <div
              className="stop-card"
              key={`${chargerName}-${stopNumber}-${index}`}
            >
              <div className="stop-header">
                <div className="stop-number">
                  {stopNumber}
                </div>

                <div>
                  <h3>{chargerName}</h3>
                  <p>
                    {stop.network ?? "Network unknown"} ·{" "}
                    {formatPower(stop.power_kw)} · Route leg{" "}
                    {stop.route_leg ?? "—"}
                  </p>
                </div>
              </div>

              <div className="summary-grid stop-grid">
                <div>
                  <span>Arrival SOC</span>
                  <strong>{formatSoc(stop.arrival_soc)}</strong>
                </div>

                <div>
                  <span>Departure SOC</span>
                  <strong>{formatSoc(stop.departure_soc)}</strong>
                </div>

                <div>
                  <span>Charging Time</span>
                  <strong>{formatNumber(chargingMinutes, 1)} min</strong>
                </div>

                <div>
                  <span>Energy Added</span>
                  <strong>{formatNumber(energyAdded, 1)} kWh</strong>
                </div>

                <div>
                  <span>Detour</span>
                  <strong>{formatNumber(detourKm, 1)} km</strong>
                </div>
              </div>

              <ReliabilityPanel
                stop={stop}
                backup={backup}
              />

              <ChargingDecisionExplanation
                stop={stop}
                summary={summary}
              />
            </div>
          );
        })}
      </div>
    </section>
  );
}