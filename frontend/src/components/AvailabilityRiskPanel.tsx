import type { ChargingStop } from "../types/trip";

interface AvailabilityRiskPanelProps {
  chargingStops: ChargingStop[];
  alternativePlansByLeg?: unknown[] | null;
  variant?: "compact" | "full";
}

type RecordValue = Record<string, unknown>;

interface BackupOption {
  chargerName: string;
  network: string;
  totalMinutes: number | null;
  chargingMinutes: number | null;
  detourMinutes: number | null;
  finalSocPercent: number | null;
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

function firstString(record: RecordValue, keys: string[]) {
  const value = firstValue(record, keys);

  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }

  if (typeof value === "number") {
    return String(value);
  }

  return null;
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

function firstBoolean(record: RecordValue, keys: string[]) {
  const value = firstValue(record, keys);

  if (typeof value === "boolean") {
    return value;
  }

  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();

    if (normalized === "true") {
      return true;
    }

    if (normalized === "false") {
      return false;
    }
  }

  return false;
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

function formatSoc(value: number | null) {
  if (value === null) {
    return "—";
  }

  return `${value.toFixed(1)}%`;
}

function chargerNameFromRecord(record: RecordValue) {
  const charger = nestedRecord(record, [
    "charger",
    "selected_charger",
    "charging_stop"
  ]);

  const stop = asRecord(asArray(record.charging_stops)[0] ?? asArray(record.stops)[0]);

  return (
    firstString(record, ["charger_name", "name", "station_name"]) ??
    firstString(stop, ["charger_name", "name", "station_name"]) ??
    firstString(charger, ["charger_name", "name", "station_name"]) ??
    "Backup charger"
  );
}

function networkFromRecord(record: RecordValue) {
  const charger = nestedRecord(record, [
    "charger",
    "selected_charger",
    "charging_stop"
  ]);

  const stop = asRecord(asArray(record.charging_stops)[0] ?? asArray(record.stops)[0]);

  return (
    firstString(record, ["network", "operator", "provider"]) ??
    firstString(stop, ["network", "operator", "provider"]) ??
    firstString(charger, ["network", "operator", "provider"]) ??
    "Network unknown"
  );
}

function selectedChargerNames(chargingStops: ChargingStop[]) {
  return new Set(
    chargingStops
      .map((stop) => {
        const record = asRecord(stop);

        return (
          firstString(record, ["charger_name", "name", "station_name"]) ??
          ""
        ).toLowerCase();
      })
      .filter(Boolean)
  );
}

function extractPlans(group: RecordValue) {
  const alternatives =
    asArray(group.alternative_plans).length > 0
      ? asArray(group.alternative_plans)
      : asArray(group.alternatives).length > 0
        ? asArray(group.alternatives)
        : asArray(group.plans).length > 0
          ? asArray(group.plans)
          : asArray(group.candidates);

  return alternatives.map(asRecord);
}

function findBackupOption(
  chargingStops: ChargingStop[],
  alternativePlansByLeg?: unknown[] | null
): BackupOption | null {
  if (!alternativePlansByLeg?.length) {
    return null;
  }

  const selectedNames = selectedChargerNames(chargingStops);

  for (const rawGroup of alternativePlansByLeg) {
    const group = asRecord(rawGroup);

    for (const plan of extractPlans(group)) {
      const name = chargerNameFromRecord(plan);

      if (selectedNames.has(name.toLowerCase())) {
        continue;
      }

      return {
        chargerName: name,
        network: networkFromRecord(plan),
        totalMinutes: firstNumber(plan, [
          "total_minutes",
          "total_time_minutes",
          "total_trip_minutes"
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
        ])
      };
    }
  }

  return null;
}

function riskForStop(stop: ChargingStop) {
  const record = asRecord(stop);

  const status = (
    firstString(record, ["availability_status", "status"]) ?? "unknown"
  ).toLowerCase();

  const isLive = firstBoolean(record, ["is_live_availability"]);
  const reliabilityLabel = (
    firstString(record, ["reliability_label"]) ?? ""
  ).toLowerCase();

  if (status === "offline" || status === "busy") {
    return {
      level: "high",
      title: "High availability risk",
      reason: "Selected charger may be busy or offline."
    };
  }

  if (status === "limited") {
    return {
      level: "medium",
      title: "Limited availability",
      reason: "Only limited availability is expected at this charger."
    };
  }

  if (!isLive || status === "unknown") {
    return {
      level: "medium",
      title: "Availability unknown",
      reason: "Live stall availability is not available for this charger."
    };
  }

  if (reliabilityLabel === "low") {
    return {
      level: "medium",
      title: "Reliability caution",
      reason: "This charger has a lower reliability score."
    };
  }

  return {
    level: "low",
    title: "Availability looks acceptable",
    reason: "No major availability risk was detected."
  };
}

function worstRisk(chargingStops: ChargingStop[]) {
  const risks = chargingStops.map(riskForStop);

  if (risks.some((risk) => risk.level === "high")) {
    return risks.find((risk) => risk.level === "high")!;
  }

  if (risks.some((risk) => risk.level === "medium")) {
    return risks.find((risk) => risk.level === "medium")!;
  }

  return risks[0];
}

export function AvailabilityRiskPanel({
  chargingStops,
  alternativePlansByLeg,
  variant = "compact"
}: AvailabilityRiskPanelProps) {
  if (chargingStops.length === 0) {
    return null;
  }

  const primaryStop = chargingStops[0];
  const stopRecord = asRecord(primaryStop);
  const risk = worstRisk(chargingStops);
  const backup = findBackupOption(chargingStops, alternativePlansByLeg);

  const primaryName =
    firstString(stopRecord, ["charger_name", "name", "station_name"]) ??
    "Selected charger";

  const source = firstString(stopRecord, ["availability_source"]);
  const recommendation =
    firstString(stopRecord, ["availability_recommendation"]) ??
    "Keep a backup charger ready before departure.";

  return (
    <section
      className={`availability-risk-card availability-risk-${risk.level} ${variant}`}
    >
      <div className="availability-risk-header">
        <div>
          <span>Availability Risk</span>
          <h3>{risk.title}</h3>
        </div>

        <strong>{risk.level}</strong>
      </div>

      <p>{risk.reason}</p>

      <div className="availability-risk-selected">
        <span>Selected stop</span>
        <strong>{primaryName}</strong>
        {source && <small>{source}</small>}
      </div>

      <div className="availability-risk-action">
        <span>Recommended action</span>
        <strong>{recommendation}</strong>
      </div>

      {backup && (
        <div className="availability-backup">
          <span>Recommended backup</span>
          <strong>{backup.chargerName}</strong>
          <small>{backup.network}</small>

          {variant === "full" && (
            <div className="availability-backup-metrics">
              <div>
                <span>Total</span>
                <strong>{formatMinutes(backup.totalMinutes)}</strong>
              </div>

              <div>
                <span>Charge</span>
                <strong>{formatMinutes(backup.chargingMinutes)}</strong>
              </div>

              <div>
                <span>Detour</span>
                <strong>{formatMinutes(backup.detourMinutes)}</strong>
              </div>

              <div>
                <span>Final SOC</span>
                <strong>{formatSoc(backup.finalSocPercent)}</strong>
              </div>
            </div>
          )}
        </div>
      )}

      {!backup && (
        <div className="availability-backup">
          <span>Recommended backup</span>
          <strong>No backup option found in current plan</strong>
          <small>Open the alternative plans section to review other options.</small>
        </div>
      )}
    </section>
  );
}