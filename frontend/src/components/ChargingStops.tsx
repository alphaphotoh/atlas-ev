import type { ChargingStop } from "../types/trip";

interface ChargingStopsProps {
  stops: ChargingStop[];
}

export function ChargingStops({
  stops
}: ChargingStopsProps) {
  if (!stops || stops.length === 0) {
    return null;
  }

  return (
    <section className="card">
      <h2>Charging Stops</h2>

      <div className="stops">
        {stops.map((stop) => (
          <div className="stop" key={`${stop.stop}-${stop.charger_name}`}>
            <h3>
              Stop {stop.stop}: {stop.charger_name}
            </h3>

            <p>
              {stop.network || "Unknown network"} ·{" "}
              {stop.power_kw ? `${stop.power_kw} kW` : "Power unknown"}
            </p>

            <div className="summary-grid">
              <div>
                <span>Arrival SOC</span>
                <strong>{stop.arrival_soc.toFixed(1)}%</strong>
              </div>

              <div>
                <span>Departure SOC</span>
                <strong>{stop.departure_soc.toFixed(1)}%</strong>
              </div>

              <div>
                <span>Charging</span>
                <strong>{stop.charging_time_minutes.toFixed(1)} min</strong>
              </div>

              <div>
                <span>Added</span>
                <strong>{stop.charge_added_kwh.toFixed(1)} kWh</strong>
              </div>

              <div>
                <span>Detour</span>
                <strong>
                  {(stop.detour_distance_km || 0).toFixed(1)} km
                </strong>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}