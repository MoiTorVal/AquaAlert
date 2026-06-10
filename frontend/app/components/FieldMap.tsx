"use client";

import "leaflet/dist/leaflet.css";
import { latLngBounds } from "leaflet";
import { MapContainer, Polygon, TileLayer } from "react-leaflet";
import { IMAGERY_ATTRIBUTION, IMAGERY_URL, LABELS_URL } from "../lib/mapTiles";
import { parseWktPolygon } from "../lib/wkt";

// Leaflet touches `window` at import time, so this component must only be
// loaded with next/dynamic({ ssr: false }).
export default function FieldMap({ wkt }: { wkt: string }) {
  const positions = parseWktPolygon(wkt);
  if (!positions) return null;

  return (
    // relative z-0 isolate traps Leaflet's internal z-indexes (up to ~1000)
    // so the map can't paint over modal overlays
    <div className="relative isolate z-0 h-64 overflow-hidden rounded-xl">
      <MapContainer
        bounds={latLngBounds(positions).pad(0.2)}
        scrollWheelZoom={false}
        className="h-full w-full"
      >
        <TileLayer attribution={IMAGERY_ATTRIBUTION} url={IMAGERY_URL} />
        <TileLayer url={LABELS_URL} />
        <Polygon
          positions={positions}
          pathOptions={{ color: "#16a34a", weight: 3, fillOpacity: 0.15 }}
        />
      </MapContainer>
    </div>
  );
}
