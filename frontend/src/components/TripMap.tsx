import { useEffect } from "react";
import L from "leaflet";
import {
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  useMap
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

import type { MapMarker, TripMapData } from "../types/trip";

interface TripMapProps {
  mapData?: TripMapData;
}

interface FitBoundsProps {
  mapData: TripMapData;
}

function FitBounds({
  mapData
}: FitBoundsProps) {
  const map = useMap();

  useEffect(() => {
    if (mapData.bounds) {
      map.fitBounds(
        [
          [
            mapData.bounds.min_latitude,
            mapData.bounds.min_longitude
          ],
          [
            mapData.bounds.max_latitude,
            mapData.bounds.max_longitude
          ]
        ],
        {
          padding: [35, 35]
        }
      );
    }
  }, [map, mapData]);

  return null;
}

function markerIcon(marker: MapMarker) {
  const label =
    marker.type === "origin"
      ? "O"
      : marker.type === "destination"
        ? "D"
        : marker.type === "charger"
          ? `${marker.stop || "C"}`
          : "W";

  return L.divIcon({
    className: `atlas-marker atlas-marker-${marker.type}`,
    html: `<span>${label}</span>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16]
  });
}

export function TripMap({
  mapData
}: TripMapProps) {
  if (!mapData || mapData.route_geometry.length === 0) {
    return null;
  }

  const routePositions = mapData.route_geometry.map((point) => {
    return [
      point[1],
      point[0]
    ] as [number, number];
  });

  const center = routePositions[0];

  return (
    <section className="card map-card">
      <div className="section-header">
        <div>
          <h2>Route Map</h2>
          <p>
            Route, waypoints, charging stops, and destination.
          </p>
        </div>

        <div className="map-legend">
          <span>O Origin</span>
          <span>W Waypoint</span>
          <span>1 Charger</span>
          <span>D Destination</span>
        </div>
      </div>

      <MapContainer
        center={center}
        zoom={8}
        className="map"
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <Polyline
          positions={routePositions}
          weight={5}
          opacity={0.85}
        />

        {mapData.markers.map((marker) => (
          <Marker
            key={`${marker.type}-${marker.label}-${marker.latitude}-${marker.longitude}`}
            position={[
              marker.latitude,
              marker.longitude
            ]}
            icon={markerIcon(marker)}
          >
            <Popup>
              <strong>{marker.label}</strong>

              {marker.charger_name && (
                <>
                  <br />
                  {marker.network || "Unknown network"}
                  <br />
                  {marker.power_kw || "?"} kW
                </>
              )}
            </Popup>
          </Marker>
        ))}

        <FitBounds mapData={mapData} />
      </MapContainer>
    </section>
  );
}