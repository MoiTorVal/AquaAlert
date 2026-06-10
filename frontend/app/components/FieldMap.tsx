"use client";

import "leaflet/dist/leaflet.css";
import { latLngBounds } from "leaflet";
import { MapContainer, Polygon, TileLayer } from "react-leaflet";
import { parseWktPolygon } from "../lib/wkt";

// Leaflet touches `window` at import time, so this component must only be
// loaded with next/dynamic({ ssr: false }).
export default function FieldMap({ wkt }: { wkt: string }) {
  const positions = parseWktPolygon(wkt);
  if (!positions) return null;

  return (
    <div className="h-64 overflow-hidden rounded-xl">
      <MapContainer
        bounds={latLngBounds(positions).pad(0.2)}
        scrollWheelZoom={false}
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polygon positions={positions} pathOptions={{ color: "#16a34a" }} />
      </MapContainer>
    </div>
  );
}
