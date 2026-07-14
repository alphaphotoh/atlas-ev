import type { RouteLeg } from "../types/trip";

interface RouteLegsProps {
  legs?: RouteLeg[];
}

function formatMinutes(minutes: number) {
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);

  if (hours <= 0) {
    return `${mins} min`;
  }

  return `${hours} hr ${mins} min`;
}

export function RouteLegs({
  legs
}: RouteLegsProps) {
  if (!legs || legs.length === 0) {
    return null;
  }

  return (
    <section className="card">
      <div className="section-header">
        <div>
          <h2>Route Legs</h2>
          <p>
            Energy, SOC, and charging status for each part of the trip.
          </p>
        </div>
      </div>

      <div className="legs">
        {legs.map((leg) => (
          <article className="route-leg" key={leg.leg}>
            <div className="route-leg-header">
              <div className="leg-number">
                {leg.leg}
              </div>

              <div>
                <h3>
                  {leg.origin} → {leg.destination}
                </h3>

                <p>
                  Status: <strong>{leg.planning_status}</strong>
                  {leg.charging_required ? " · Charging required" : " · No charge needed"}
                </p>
              </div>
            </div>

            <div className="summary-grid leg-grid">
              <div>
                <span>Distance</span>
                <strong>{leg.distance_km.toFixed(1)} km</strong>
              </div>

              <div>
                <span>Driving Time</span>
                <strong>{formatMinutes(leg.duration_minutes)}</strong>
              </div>

              <div>
                <span>Energy</span>
                <strong>{leg.energy_kwh.toFixed(1)} kWh</strong>
              </div>

              <div>
                <span>SOC Without Charge</span>
                <strong>{leg.arrival_soc_without_charging.toFixed(1)}%</strong>
              </div>

              <div>
                <span>SOC With Charge</span>
                <strong>{leg.arrival_soc_with_charging.toFixed(1)}%</strong>
              </div>

              <div>
                <span>Charging Stops</span>
                <strong>
                  {leg.charging_stop_numbers.length > 0
                    ? leg.charging_stop_numbers.join(", ")
                    : "None"}
                </strong>
              </div>
            </div>

            {leg.warnings.length > 0 && (
              <div className="warnings route-leg-warnings">
                {leg.warnings.map((warning) => (
                  <p key={warning}>{warning}</p>
                ))}
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}