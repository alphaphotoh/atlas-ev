import { FormEvent, useState } from "react";

import type {
  TripConditions,
  TripRequest,
  WaypointMode
} from "../types/trip";

interface TripFormProps {
  onSubmit: (request: TripRequest) => void;
  loading: boolean;
}

function parseWaypoints(value: string) {
  return value
    .split(/\r?\n/)
    .map((waypoint) => waypoint.trim())
    .filter(Boolean);
}

function optionalNumber(value: string) {
  const cleaned = value.trim();

  if (!cleaned) {
    return undefined;
  }

  const parsed = Number(cleaned);

  if (!Number.isFinite(parsed)) {
    return undefined;
  }

  return parsed;
}

function optionalText(value: string) {
  const cleaned = value.trim();

  if (!cleaned) {
    return undefined;
  }

  return cleaned;
}

function hasConditionValue(conditions: TripConditions) {
  return Object.keys(conditions).length > 0;
}

export function TripForm({
  onSubmit,
  loading
}: TripFormProps) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [waypoints, setWaypoints] = useState("Kingston, ON\ncornwall, ON");
  const [waypointMode, setWaypointMode] = useState<WaypointMode>("via_points");

  const [startingSoc, setStartingSoc] = useState("100");

  const [showConditions, setShowConditions] = useState(false);

  const [passengers, setPassengers] = useState("");
  const [cargoWeightKg, setCargoWeightKg] = useState("");
  const [climateControl, setClimateControl] = useState("");
  const [cabinTargetTempC, setCabinTargetTempC] = useState("");
  const [drivingStyle, setDrivingStyle] = useState("");
  const [roadCondition, setRoadCondition] = useState("");
  const [tireCondition, setTireCondition] = useState("");
  const [roofLoad, setRoofLoad] = useState("");
  const [batteryDegradationPercent, setBatteryDegradationPercent] =
    useState("");

  function buildTripConditions() {
    const conditions: TripConditions = {};

    const parsedPassengers = optionalNumber(passengers);
    const parsedCargo = optionalNumber(cargoWeightKg);
    const parsedCabinTarget = optionalNumber(cabinTargetTempC);
    const parsedBatteryDegradation = optionalNumber(
      batteryDegradationPercent
    );

    if (parsedPassengers !== undefined) {
      conditions.passengers = parsedPassengers;
    }

    if (parsedCargo !== undefined) {
      conditions.cargo_weight_kg = parsedCargo;
    }

    if (optionalText(climateControl)) {
      conditions.climate_control = climateControl;
    }

    if (parsedCabinTarget !== undefined) {
      conditions.cabin_target_temp_c = parsedCabinTarget;
    }

    if (optionalText(drivingStyle)) {
      conditions.driving_style = drivingStyle;
    }

    if (optionalText(roadCondition)) {
      conditions.road_condition = roadCondition;
    }

    if (optionalText(tireCondition)) {
      conditions.tire_condition = tireCondition;
    }

    if (optionalText(roofLoad)) {
      conditions.roof_load = roofLoad;
    }

    if (parsedBatteryDegradation !== undefined) {
      conditions.battery_degradation_percent = parsedBatteryDegradation;
    }

    if (!hasConditionValue(conditions)) {
      return undefined;
    }

    return conditions;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const tripConditions = buildTripConditions();

    const request: TripRequest = {
      vehicle: "vf9",
      origin,
      destination,
      waypoints: parseWaypoints(waypoints),
      waypoint_mode: waypointMode,
      starting_soc: Number(startingSoc),
      average_speed: 90,
      traffic_mode: "live",
      traffic_level: undefined
    };

    if (tripConditions) {
      request.trip_conditions = tripConditions;
    }

    onSubmit(request);
  }

  function resetConditions() {
    setPassengers("");
    setCargoWeightKg("");
    setClimateControl("");
    setCabinTargetTempC("");
    setDrivingStyle("");
    setRoadCondition("");
    setTireCondition("");
    setRoofLoad("");
    setBatteryDegradationPercent("");
  }

  return (
    <section className="card">
      <div className="section-header">
        <div>
          <h2>Plan Trip</h2>
          <p>
            Required route fields first. Optional trip conditions can be left
            blank.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="trip-form">
        <div className="form-grid">
          <label>
            Origin
            <input
              value={origin}
              onChange={(event) => setOrigin(event.target.value)}
              required
            />
          </label>

          <label>
            Destination
            <input
              value={destination}
              onChange={(event) => setDestination(event.target.value)}
              required
            />
          </label>

          <label className="wide-field">
            Waypoints
            <textarea
              value={waypoints}
              onChange={(event) => setWaypoints(event.target.value)}
              rows={3}
              placeholder="One waypoint per line"
            />
          </label>

          <label>
            Waypoint Mode
            <select
              value={waypointMode}
              onChange={(event) =>
                setWaypointMode(event.target.value as WaypointMode)
              }
            >
              <option value="via_points">
                Via points only — shape route
              </option>
              <option value="required_stops">
                Required stops — separate trip legs
              </option>
            </select>
          </label>

          <label>
            Starting SOC %
            <input
              type="number"
              min="1"
              max="100"
              value={startingSoc}
              onChange={(event) => setStartingSoc(event.target.value)}
              required
            />
          </label>
</div>

        <div className="optional-section">
          <button
            className="condition-toggle"
            type="button"
            onClick={() => setShowConditions(!showConditions)}
          >
            {showConditions
              ? "Hide Optional Trip Conditions"
              : "Show Optional Trip Conditions"}
          </button>

          <p className="condition-help">
            These are optional. Leave anything blank and Atlas will ignore it.
          </p>

          {showConditions && (
            <div className="conditions-panel">
              <div className="conditions-grid">
                <label>
                  Passengers
                  <input
                    type="number"
                    min="1"
                    max="8"
                    value={passengers}
                    onChange={(event) => setPassengers(event.target.value)}
                    placeholder="Optional"
                  />
                </label>

                <label>
                  Cargo Weight kg
                  <input
                    type="number"
                    min="0"
                    value={cargoWeightKg}
                    onChange={(event) => setCargoWeightKg(event.target.value)}
                    placeholder="Optional"
                  />
                </label>

                <label>
                  Climate Control
                  <select
                    value={climateControl}
                    onChange={(event) => setClimateControl(event.target.value)}
                  >
                    <option value="">Not specified</option>
                    <option value="off">Off</option>
                    <option value="eco">Eco</option>
                    <option value="normal">Normal</option>
                    <option value="high">High heat / AC</option>
                  </select>
                </label>

                <label>
                  Cabin Target °C
                  <input
                    type="number"
                    value={cabinTargetTempC}
                    onChange={(event) =>
                      setCabinTargetTempC(event.target.value)
                    }
                    placeholder="Optional"
                  />
                </label>

                <label>
                  Driving Style
                  <select
                    value={drivingStyle}
                    onChange={(event) => setDrivingStyle(event.target.value)}
                  >
                    <option value="">Not specified</option>
                    <option value="eco">Eco</option>
                    <option value="normal">Normal</option>
                    <option value="sport">Sport</option>
                    <option value="aggressive">Aggressive</option>
                  </select>
                </label>

                <label>
                  Road Condition
                  <select
                    value={roadCondition}
                    onChange={(event) => setRoadCondition(event.target.value)}
                  >
                    <option value="">Not specified</option>
                    <option value="dry">Dry</option>
                    <option value="wet">Wet</option>
                    <option value="snow">Snow</option>
                    <option value="ice">Ice</option>
                  </select>
                </label>

                <label>
                  Tire Condition
                  <select
                    value={tireCondition}
                    onChange={(event) => setTireCondition(event.target.value)}
                  >
                    <option value="">Not specified</option>
                    <option value="normal">Normal</option>
                    <option value="low_pressure">Low pressure</option>
                    <option value="winter_tires">Winter tires</option>
                  </select>
                </label>

                <label>
                  Roof Load
                  <select
                    value={roofLoad}
                    onChange={(event) => setRoofLoad(event.target.value)}
                  >
                    <option value="">Not specified</option>
                    <option value="none">None</option>
                    <option value="roof_rack">Roof rack</option>
                    <option value="cargo_box">Cargo box</option>
                  </select>
                </label>

                <label>
                  Battery Degradation %
                  <input
                    type="number"
                    min="0"
                    max="40"
                    value={batteryDegradationPercent}
                    onChange={(event) =>
                      setBatteryDegradationPercent(event.target.value)
                    }
                    placeholder="Optional"
                  />
                </label>
              </div>

              <div className="condition-actions">
                <button
                  type="button"
                  className="secondary-share-button"
                  onClick={resetConditions}
                >
                  Clear Conditions
                </button>
              </div>
            </div>
          )}
        </div>

        <button
          className="primary-button"
          type="submit"
          disabled={loading}
        >
          {loading ? "Planning..." : "Plan Trip"}
        </button>
      </form>
    </section>
  );
}