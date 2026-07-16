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
  arrivalSocPercent: number | null;
  departureSocPercent: number | null;
}

interface RiskResult {
  level: "low" | "medium" | "high";
  title: string;
  reason: string;
  action: string;
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

function firstStopRecord(record: RecordValue) {
  return asRecord(
    asArray(record.charging_stops)[0] ??
      asArray(record.stops)[0] ??
      record.charging_stop
  );
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

function formatDelta(value: number | null, unit: string) {
  if (value === null) {
    return "—";
  }

  const sign = value > 0 ? "+" : "";

  return `${sign}${value.toFixed(1)} ${unit}`;
}

function chargerNameFromRecord(record: RecordValue) {
  const charger = nestedRecord(record, [
    "charger",
    "selected_charger",
    "charging_stop"
  ]);

  const stop = firstStopRecord(record);

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

  const stop = firstStopRecord(record);

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

function planNumber(plan: RecordValue, stop: RecordValue, keys: string[]) {
  return firstNumber(plan, keys) ?? firstNumber(stop, keys);
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
      const stop = firstStopRecord(plan);
      const name = chargerNameFromRecord(plan);

      if (selectedNames.has(name.toLowerCase())) {
        continue;
      }

      return {
        chargerName: name,
        network: networkFromRecord(plan),
        totalMinutes: planNumber(plan, stop, [
          "total_minutes",
          "total_time_minutes",
          "total_trip_minutes"
        ]),
        chargingMinutes: planNumber(plan, stop, [
          "charging_minutes",
          "charging_time_minutes",
          "total_charging_minutes"
        ]),
        detourMinutes: planNumber(plan, stop, [
          "detour_minutes",
          "total_detour_minutes"
        ]),
        finalSocPercent: planNumber(plan, stop, [
          "final_soc_percent",
          "final_arrival_soc",
          "arrival_soc_at_destination_percent",
          "destination_arrival_soc_percent"
        ]),
        arrivalSocPercent: planNumber(plan, stop, [
          "arrival_soc_percent",
          "arrival_soc",
          "charger_arrival_soc_percent"
        ]),
        departureSocPercent: planNumber(plan, stop, [
          "departure_soc_percent",
          "departure_soc",
          "charger_departure_soc_percent"
        ])
      };
    }
  }

  return null;
}

function riskForStop(stop: ChargingStop): RiskResult {
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
      reason: "Selected charger may be busy or offline.",
      action: "Use the backup charger before relying on this stop."
    };
  }

  if (status === "limited") {
    return {
      level: "medium",
      title: "Limited availability",
      reason: "Only limited availability is expected at this charger.",
      action: "Keep the selected stop, but prepare the backup charger."
    };
  }

  if (!isLive || status === "unknown") {
    return {
      level: "medium",
      title: "Availability unknown",
      reason: "Live stall availability is not available for this charger.",
      action: "Keep the selected stop, but prepare the backup charger."
    };
  }

  if (reliabilityLabel === "low") {
    return {
      level: "medium",
      title: "Reliability caution",
      reason: "This charger has a lower reliability score.",
      action: "Keep the selected stop, but review the backup charger."
    };
  }

  return {
    level: "low",
    title: "Availability looks acceptable",
    reason: "No major availability risk was detected.",
    action: "Proceed with the selected charging stop."
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

function selectedMetrics(stop: ChargingStop) {
  const record = asRecord(stop);

  return {
    chargingMinutes: firstNumber(record, [
      "charging_minutes",
      "charging_time_minutes",
      "charge_time_minutes"
    ]),
    detourMinutes: firstNumber(record, [
      "detour_minutes",
      "estimated_detour_minutes"
    ]),
    arrivalSocPercent: firstNumber(record, [
      "arrival_soc_percent",
      "arrival_soc",
      "charger_arrival_soc_percent"
    ]),
    departureSocPercent: firstNumber(record, [
      "departure_soc_percent",
      "departure_soc",
      "charger_departure_soc_percent"
    ])
  };
}

function deltaClass(
  value: number | null,
  lowerIsBetter = true
) {
  if (value === null || value === 0) {
    return "delta-neutral";
  }

  const good = lowerIsBetter ? value < 0 : value > 0;

  return good ? "delta-good" : "delta-caution";
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
  const selected = selectedMetrics(primaryStop);
  const risk = worstRisk(chargingStops);
  const backup = findBackupOption(chargingStops, alternativePlansByLeg);

  const primaryName =
    firstString(stopRecord, ["charger_name", "name", "station_name"]) ??
    "Selected charger";

  const source = firstString(stopRecord, ["availability_source"]);
  const recommendation =
    firstString(stopRecord, ["availability_recommendation"]) ??
    risk.action;

  const backupChargingDelta =
    backup !== null &&
    backup.chargingMinutes !== null &&
    selected.chargingMinutes !== null
      ? backup.chargingMinutes - selected.chargingMinutes
      : null;

  const backupDetourDelta =
    backup !== null &&
    backup.detourMinutes !== null &&
    selected.detourMinutes !== null
      ? backup.detourMinutes - selected.detourMinutes
      : null;

  const backupSocDelta =
    backup?.finalSocPercent !== null && backup?.finalSocPercent !== undefined
      ? null
      : null;

  const isSaferBackup =
    Boolean(backup) && (risk.level === "medium" || risk.level === "high");

  return (
    <section
      className={`availability-risk-card availability-risk-${risk.level} ${variant}`}
    >
      <div className="availability-risk-header">
        <div>
          <span>Availability Risk</span>
          <h3>
            {isSaferBackup ? "Safer backup ready" : risk.title}
          </h3>
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
        <div className="availability-backup safer-backup">
          <div className="availability-backup-header">
            <div>
              <span>{isSaferBackup ? "Safer backup" : "Recommended backup"}</span>
              <strong>{backup.chargerName}</strong>
              <small>{backup.network}</small>
            </div>

            {isSaferBackup && <em>Keep ready</em>}
          </div>

          <div className="availability-selected-vs-backup">
            <article>
              <span>Selected</span>
              <strong>{primaryName}</strong>
              <small>
                {formatMinutes(selected.chargingMinutes)} charge ·{" "}
                {formatMinutes(selected.detourMinutes)} detour
              </small>
              <small>
                SOC {formatSoc(selected.arrivalSocPercent)} →{" "}
                {formatSoc(selected.departureSocPercent)}
              </small>
            </article>

            <article className="backup-option-card">
              <span>Backup</span>
              <strong>{backup.chargerName}</strong>
              <small>
                {formatMinutes(backup.chargingMinutes)} charge ·{" "}
                {formatMinutes(backup.detourMinutes)} detour
              </small>
              <small>
                SOC {formatSoc(backup.arrivalSocPercent)} →{" "}
                {formatSoc(backup.departureSocPercent)}
              </small>
            </article>
          </div>

          {variant === "full" && (
            <div className="availability-backup-metrics">
              <div>
                <span>Backup total</span>
                <strong>{formatMinutes(backup.totalMinutes)}</strong>
              </div>

              <div>
                <span>Charge difference</span>
                <strong className={deltaClass(backupChargingDelta)}>
                  {formatDelta(backupChargingDelta, "min")}
                </strong>
              </div>

              <div>
                <span>Detour difference</span>
                <strong className={deltaClass(backupDetourDelta)}>
                  {formatDelta(backupDetourDelta, "min")}
                </strong>
              </div>

              <div>
                <span>Backup final SOC</span>
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