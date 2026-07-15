import { useMemo, useState } from "react";

import type {
  ChargingStop,
  TripResponse
} from "../types/trip";

interface GoogleMapsShareProps {
  trip: TripResponse;
  chargingStops: ChargingStop[];
}

interface SharePoint {
  label: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  type: "waypoint" | "charger";
  routeOrderKm: number;
}

const GOOGLE_MAPS_MAX_WAYPOINTS = 9;

function isValidCoordinate(
  latitude?: number | null,
  longitude?: number | null
) {
  return (
    latitude !== null &&
    latitude !== undefined &&
    longitude !== null &&
    longitude !== undefined &&
    Number.isFinite(latitude) &&
    Number.isFinite(longitude)
  );
}

function googlePoint(
  point: SharePoint
) {
  if (point.address) {
    return point.address;
  }

  if (
    point.latitude !== undefined &&
    point.longitude !== undefined
  ) {
    return `${point.latitude.toFixed(6)},${point.longitude.toFixed(6)}`;
  }

  return point.label;
}

function chargerName(
  stop: ChargingStop
) {
  return stop.charger_name ?? stop.name ?? "Charging stop";
}

function fallbackWaypointOrderKm(
  trip: TripResponse,
  index: number,
  totalWaypoints: number
) {
  const distance = trip.summary?.distance_km ?? 0;

  if (distance <= 0 || totalWaypoints <= 0) {
    return index + 1;
  }

  return (
    ((index + 1) * distance) /
    (totalWaypoints + 1)
  );
}

function chargerRouteOrderKm(
  trip: TripResponse,
  stop: ChargingStop,
  fallbackIndex: number
) {
  if (
    stop.route_distance_km !== null &&
    stop.route_distance_km !== undefined
  ) {
    return stop.route_distance_km;
  }

  const distance = trip.summary?.distance_km ?? 0;

  if (distance <= 0) {
    return 1000 + fallbackIndex;
  }

  return (
    ((fallbackIndex + 1) * distance) /
    (fallbackIndex + 2)
  );
}

function buildSharePoints(
  trip: TripResponse,
  chargingStops: ChargingStop[]
): SharePoint[] {
  const points: SharePoint[] = [];
  const seen = new Set<string>();

  const typedWaypoints = trip.waypoints ?? [];

  typedWaypoints.forEach((waypoint, index) => {
    const cleaned = waypoint.trim();

    if (!cleaned) {
      return;
    }

    const key = `waypoint:${cleaned.toLowerCase()}`;

    if (seen.has(key)) {
      return;
    }

    seen.add(key);

    points.push({
      label: cleaned,
      address: cleaned,
      type: "waypoint",
      routeOrderKm: fallbackWaypointOrderKm(
        trip,
        index,
        typedWaypoints.length
      )
    });
  });

  chargingStops.forEach((stop, index) => {
    if (!isValidCoordinate(stop.latitude, stop.longitude)) {
      return;
    }

    const key = (
      `charger:${stop.latitude.toFixed(5)},` +
      `${stop.longitude.toFixed(5)}`
    );

    if (seen.has(key)) {
      return;
    }

    seen.add(key);

    points.push({
      label: `${index + 1}. ${chargerName(stop)}`,
      latitude: stop.latitude,
      longitude: stop.longitude,
      type: "charger",
      routeOrderKm: chargerRouteOrderKm(
        trip,
        stop,
        index
      )
    });
  });

  points.sort((first, second) => {
    if (first.routeOrderKm !== second.routeOrderKm) {
      return first.routeOrderKm - second.routeOrderKm;
    }

    if (first.type === second.type) {
      return first.label.localeCompare(second.label);
    }

    return first.type === "waypoint" ? -1 : 1;
  });

  return points;
}

function buildGoogleMapsUrl(
  trip: TripResponse,
  points: SharePoint[]
) {
  const includedPoints = points.slice(
    0,
    GOOGLE_MAPS_MAX_WAYPOINTS
  );

  const params = new URLSearchParams();

  params.set("api", "1");
  params.set("origin", trip.origin);
  params.set("destination", trip.destination);
  params.set("travelmode", "driving");

  if (includedPoints.length > 0) {
    params.set(
      "waypoints",
      includedPoints.map(googlePoint).join("|")
    );
  }

  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

export function GoogleMapsShare({
  trip,
  chargingStops
}: GoogleMapsShareProps) {
  const [copied, setCopied] = useState(false);

  const sharePoints = useMemo(
    () => buildSharePoints(
      trip,
      chargingStops
    ),
    [
      trip,
      chargingStops
    ]
  );

  const includedPoints = sharePoints.slice(
    0,
    GOOGLE_MAPS_MAX_WAYPOINTS
  );

  const omittedCount = Math.max(
    sharePoints.length - includedPoints.length,
    0
  );

  const googleMapsUrl = useMemo(
    () => buildGoogleMapsUrl(
      trip,
      sharePoints
    ),
    [
      trip,
      sharePoints
    ]
  );

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(
        googleMapsUrl
      );

      setCopied(true);

      window.setTimeout(
        () => setCopied(false),
        2000
      );
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="card google-share-card">
      <div className="section-header">
        <div>
          <h2>Share Route</h2>
          <p>
            Open this trip in Google Maps with typed waypoints and charging
            stops in route order.
          </p>
        </div>

        <div className="share-actions">
          <a
            className="share-button"
            href={googleMapsUrl}
            target="_blank"
            rel="noreferrer"
          >
            Open in Google Maps
          </a>

          <button
            className="secondary-share-button"
            type="button"
            onClick={copyLink}
          >
            {copied ? "Copied" : "Copy Link"}
          </button>
        </div>
      </div>

      <div className="share-note">
        Google Maps recalculates the route using Google routing and traffic.
        Distance and driving time may differ from Atlas.
      </div>

      <div className="share-route-list">
        <div>
          <span>Origin</span>
          <strong>{trip.origin}</strong>
        </div>

        {includedPoints.map((point, index) => (
          <div key={`${point.type}-${point.label}-${index}`}>
            <span>
              Stop {index + 1} ·{" "}
              {point.type === "charger" ? "Charging" : "Waypoint"}
            </span>
            <strong>{point.label}</strong>
            {point.address ? (
              <small>{point.address}</small>
            ) : (
              <small>
                {point.latitude?.toFixed(5)}, {point.longitude?.toFixed(5)}
              </small>
            )}
          </div>
        ))}

        <div>
          <span>Destination</span>
          <strong>{trip.destination}</strong>
        </div>
      </div>

      {omittedCount > 0 && (
        <div className="share-warning">
          Google Maps URL waypoint limits can prevent all stops from opening in
          one route. {omittedCount} extra stop
          {omittedCount === 1 ? "" : "s"} were not included in the link.
        </div>
      )}
    </section>
  );
}