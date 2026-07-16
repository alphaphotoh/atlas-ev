interface AlternativePlansProps {
  alternativePlansByLeg?: unknown[] | null;
}

type RecordValue = Record<string, unknown>;

interface NormalizedPlan {
  id: string;
  label: string;
  isRecommended: boolean;
  chargerName: string;
  network: string;
  powerKw: number | null;
  totalMinutes: number | null;
  chargingMinutes: number | null;
  detourMinutes: number | null;
  finalSocPercent: number | null;
  arrivalSocPercent: number | null;
  departureSocPercent: number | null;
  energyAddedKwh: number | null;
}

interface NormalizedGroup {
  routeLeg: string;
  plans: NormalizedPlan[];
}

function asRecord(value: unknown): RecordValue {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as RecordValue;
  }

  return {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function firstValue(record: RecordValue, keys: string[]) {
  for (const key of keys) {
    const value = record[key];

    if (value !== undefined && value !== null) {
      return value;
    }
  }

  return undefined;
}

function firstNumber(record: RecordValue, keys: string[]) {
  const value = firstValue(record, keys);

  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string") {
    const parsed = Number(value);

    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return null;
}

function firstString(record: RecordValue, keys: string[]) {
  const value = firstValue(record, keys);

  if (typeof value === "string" && value.trim()) {
    return value;
  }

  if (typeof value === "number") {
    return String(value);
  }

  return null;
}

function nestedRecord(record: RecordValue, keys: string[]) {
  for (const key of keys) {
    const value = record[key];

    if (value && typeof value === "object" && !Array.isArray(value)) {
      return value as RecordValue;
    }
  }

  return {};
}

function formatMinutes(value: number | null) {
  if (value === null) {
    return "—";
  }

  const rounded = Math.round(value);

  if (rounded < 60) {
    return `${rounded} min`;
  }

  const hours = Math.floor(rounded / 60);
  const minutes = rounded % 60;

  if (minutes === 0) {
    return `${hours} hr`;
  }

  return `${hours} hr ${minutes} min`;
}

function formatNumber(value: number | null, digits = 1) {
  if (value === null) {
    return "—";
  }

  return value.toFixed(digits);
}

function chargerName(plan: RecordValue) {
  const charger = nestedRecord(plan, [
    "charger",
    "selected_charger",
    "charging_stop"
  ]);

  return (
    firstString(plan, ["charger_name", "name", "station_name"]) ??
    firstString(charger, ["charger_name", "name", "station_name"]) ??
    "Charging plan"
  );
}

function chargerNetwork(plan: RecordValue) {
  const charger = nestedRecord(plan, [
    "charger",
    "selected_charger",
    "charging_stop"
  ]);

  return (
    firstString(plan, ["network", "operator", "provider"]) ??
    firstString(charger, ["network", "operator", "provider"]) ??
    "Network unknown"
  );
}

function chargerPower(plan: RecordValue) {
  const charger = nestedRecord(plan, [
    "charger",
    "selected_charger",
    "charging_stop"
  ]);

  return (
    firstNumber(plan, ["power_kw", "max_power_kw", "charger_power_kw"]) ??
    firstNumber(charger, ["power_kw", "max_power_kw", "charger_power_kw"])
  );
}

function normalizePlan(
  value: unknown,
  index: number,
  isRecommended: boolean
): NormalizedPlan {
  const plan = asRecord(value);

  return {
    id: `${isRecommended ? "recommended" : "alternative"}-${index}`,
    label: isRecommended ? "Recommended" : `Alternative ${index}`,
    isRecommended,
    chargerName: chargerName(plan),
    network: chargerNetwork(plan),
    powerKw: chargerPower(plan),
    totalMinutes: firstNumber(plan, [
      "total_minutes",
      "total_time_minutes",
      "total_trip_minutes",
      "duration_minutes"
    ]),
    chargingMinutes: firstNumber(plan, [
      "charging_minutes",
      "charging_time_minutes",
      "total_charging_minutes"
    ]),
    detourMinutes: firstNumber(plan, [
      "detour_minutes",
      "total_detour_minutes"
    ]),
    finalSocPercent: firstNumber(plan, [
      "final_soc_percent",
      "arrival_soc_at_destination_percent",
      "destination_arrival_soc_percent"
    ]),
    arrivalSocPercent: firstNumber(plan, [
      "arrival_soc_percent",
      "charger_arrival_soc_percent"
    ]),
    departureSocPercent: firstNumber(plan, [
      "departure_soc_percent",
      "charger_departure_soc_percent"
    ]),
    energyAddedKwh: firstNumber(plan, [
      "energy_added_kwh",
      "charge_added_kwh"
    ])
  };
}

function extractPlans(group: RecordValue) {
  const recommended =
    group.recommended ??
    group.recommended_plan ??
    group.selected_plan ??
    null;

  const alternatives =
    asArray(group.alternative_plans).length > 0
      ? asArray(group.alternative_plans)
      : asArray(group.alternatives).length > 0
        ? asArray(group.alternatives)
        : asArray(group.plans).length > 0
          ? asArray(group.plans)
          : asArray(group.candidates);

  const plans: NormalizedPlan[] = [];

  if (recommended) {
    plans.push(normalizePlan(recommended, 0, true));
  }

  alternatives.slice(0, 4).forEach((plan, index) => {
    const normalized = normalizePlan(plan, index + 1, false);

    const duplicateRecommended =
      plans.length > 0 &&
      normalized.chargerName === plans[0].chargerName &&
      normalized.network === plans[0].network;

    if (!duplicateRecommended) {
      plans.push(normalized);
    }
  });

  return plans;
}

function normalizeGroups(
  alternativePlansByLeg?: unknown[] | null
): NormalizedGroup[] {
  if (!alternativePlansByLeg?.length) {
    return [];
  }

  return alternativePlansByLeg
    .map((value, index) => {
      const group = asRecord(value);

      const routeLeg =
        firstValue(group, ["route_leg", "routeLeg", "leg", "leg_number"]) ??
        index + 1;

      return {
        routeLeg: String(routeLeg),
        plans: extractPlans(group)
      };
    })
    .filter((group) => group.plans.length > 0);
}

function bestClass(
  value: number | null,
  bestValue: number | null,
  lowerIsBetter = true
) {
  if (value === null || bestValue === null) {
    return "";
  }

  const isBest = lowerIsBetter ? value <= bestValue : value >= bestValue;

  return isBest ? "best-metric" : "";
}

export function AlternativePlans({
  alternativePlansByLeg
}: AlternativePlansProps) {
  const groups = normalizeGroups(alternativePlansByLeg);

  if (groups.length === 0) {
    return null;
  }

  return (
    <section className="card alternative-plans-card">
      <div className="section-header">
        <div>
          <h2>Alternative Charging Plans</h2>
          <p>
            Compare the selected charger with backup options by time, SOC,
            detour, and charging details.
          </p>
        </div>
      </div>

      <div className="alternative-groups">
        {groups.map((group) => {
          const totalValues = group.plans
            .map((plan) => plan.totalMinutes)
            .filter((value): value is number => value !== null);

          const chargingValues = group.plans
            .map((plan) => plan.chargingMinutes)
            .filter((value): value is number => value !== null);

          const detourValues = group.plans
            .map((plan) => plan.detourMinutes)
            .filter((value): value is number => value !== null);

          const finalSocValues = group.plans
            .map((plan) => plan.finalSocPercent)
            .filter((value): value is number => value !== null);

          const bestTotal =
            totalValues.length > 0 ? Math.min(...totalValues) : null;

          const bestCharging =
            chargingValues.length > 0 ? Math.min(...chargingValues) : null;

          const bestDetour =
            detourValues.length > 0 ? Math.min(...detourValues) : null;

          const bestFinalSoc =
            finalSocValues.length > 0 ? Math.max(...finalSocValues) : null;

          return (
            <div className="alternative-group" key={group.routeLeg}>
              <h3>Route Leg {group.routeLeg}</h3>

              <div className="alternative-plan-grid">
                {group.plans.map((plan) => (
                  <article
                    className={
                      plan.isRecommended
                        ? "alternative-plan recommended-plan"
                        : "alternative-plan"
                    }
                    key={plan.id}
                  >
                    <div className="alternative-plan-header">
                      <span>{plan.label}</span>
                      {plan.isRecommended && <strong>Selected</strong>}
                    </div>

                    <h4>{plan.chargerName}</h4>
                    <p>{plan.network}</p>

                    <div className="alternative-metrics">
                      <div className={bestClass(plan.totalMinutes, bestTotal)}>
                        <span>Total Time</span>
                        <strong>{formatMinutes(plan.totalMinutes)}</strong>
                      </div>

                      <div
                        className={bestClass(
                          plan.chargingMinutes,
                          bestCharging
                        )}
                      >
                        <span>Charging</span>
                        <strong>{formatMinutes(plan.chargingMinutes)}</strong>
                      </div>

                      <div className={bestClass(plan.detourMinutes, bestDetour)}>
                        <span>Detour</span>
                        <strong>{formatMinutes(plan.detourMinutes)}</strong>
                      </div>

                      <div
                        className={bestClass(
                          plan.finalSocPercent,
                          bestFinalSoc,
                          false
                        )}
                      >
                        <span>Final SOC</span>
                        <strong>
                          {plan.finalSocPercent === null
                            ? "—"
                            : `${formatNumber(plan.finalSocPercent)}%`}
                        </strong>
                      </div>

                      <div>
                        <span>Arrive / Leave</span>
                        <strong>
                          {plan.arrivalSocPercent === null &&
                          plan.departureSocPercent === null
                            ? "—"
                            : `${formatNumber(
                                plan.arrivalSocPercent
                              )}% → ${formatNumber(
                                plan.departureSocPercent
                              )}%`}
                        </strong>
                      </div>

                      <div>
                        <span>Energy Added</span>
                        <strong>
                          {plan.energyAddedKwh === null
                            ? "—"
                            : `${formatNumber(plan.energyAddedKwh)} kWh`}
                        </strong>
                      </div>

                      <div>
                        <span>Power</span>
                        <strong>
                          {plan.powerKw === null
                            ? "—"
                            : `${formatNumber(plan.powerKw, 0)} kW`}
                        </strong>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}