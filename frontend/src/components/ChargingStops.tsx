import type {
  ChargingStop,
  TripSummary
} from "../types/trip";

interface ChargingStopsProps {
  stops: ChargingStop[];
  summary?: TripSummary;
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
  summary
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