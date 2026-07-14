import type { ChargingStop } from "../types/trip";

interface ChargingStopsProps {
  stops: ChargingStop[];
}

function stopNumber(stop: ChargingStop, index: number) {
  return stop.stop || stop.number || index + 1;
}

function chargerName(stop: ChargingStop) {
  return stop.charger_name || stop.name || "Unknown charger";
}

function numberValue(value: number | undefined | null) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  return 0;
}

function chargingMinutes(stop: ChargingStop) {
  return numberValue(
    stop.charging_time_minutes ??
      stop.charging_minutes ??
      stop.charge_time_minutes ??
      stop.duration_minutes
  );
}

function energyAdded(stop: ChargingStop) {
  return numberValue(
    stop.charge_added_kwh ??
      stop.energy_added_kwh
  );
}

function detourKm(stop: ChargingStop) {
  return numberValue(
    stop.detour_distance_km ??
      stop.detour_km
  );
}

export function ChargingStops({
  stops
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
      <div className="section-header">
        <div>
          <h2>Charging Stops</h2>
          <p>{stops.length} planned stop{stops.length === 1 ? "" : "s"}</p>
        </div>
      </div>

      <div className="stops">
        {stops.map((stop, index) => (
          <article
            className="stop"
            key={`${index}-${chargerName(stop)}-${stop.latitude}-${stop.longitude}`}
          >
            <div className="stop-header">
              <div className="stop-number">
                {stopNumber(stop, index)}
              </div>

              <div>
                <h3>{chargerName(stop)}</h3>
                <p>
                  {stop.network || "Unknown network"} ·{" "}
                  {stop.power_kw ? `${stop.power_kw} kW` : "Power unknown"}
                  {stop.route_leg ? ` · Route leg ${stop.route_leg}` : ""}
                </p>
              </div>
            </div>

            <div className="summary-grid stop-grid">
              <div>
                <span>Arrival SOC</span>
                <strong>{numberValue(stop.arrival_soc).toFixed(1)}%</strong>
              </div>

              <div>
                <span>Departure SOC</span>
                <strong>{numberValue(stop.departure_soc).toFixed(1)}%</strong>
              </div>

              <div>
                <span>Charging Time</span>
                <strong>{chargingMinutes(stop).toFixed(1)} min</strong>
              </div>

              <div>
                <span>Energy Added</span>
                <strong>{energyAdded(stop).toFixed(1)} kWh</strong>
              </div>

              <div>
                <span>Detour</span>
                <strong>{detourKm(stop).toFixed(1)} km</strong>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}