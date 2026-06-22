"use client";

import "leaflet/dist/leaflet.css";
import { useMemo, useState } from "react";
import { latLngBounds, type LatLngExpression } from "leaflet";
import { ImageOverlay, MapContainer, Polygon, TileLayer } from "react-leaflet";
import { IMAGERY_ATTRIBUTION, IMAGERY_URL, LABELS_URL } from "../lib/mapTiles";
import { gridToImageData } from "../lib/ndvi";

const FIELD_POSITIONS: LatLngExpression[] = [
  [36.706, -119.735],
  [36.706, -119.715],
  [36.693, -119.715],
  [36.693, -119.735],
];

// Low NDVI in the center/right to simulate stress pockets.
const MOCK_NDVI_GRID: Array<Array<number | null>> = [
  [0.72, 0.71, 0.69, 0.66, 0.62, 0.58, 0.57, 0.55],
  [0.73, 0.7, 0.67, 0.61, 0.52, 0.45, 0.42, 0.4],
  [0.71, 0.68, 0.62, 0.51, 0.41, 0.35, 0.33, 0.31],
  [0.69, 0.64, 0.55, 0.46, 0.38, 0.32, 0.3, 0.29],
  [0.67, 0.61, 0.53, 0.43, 0.36, 0.31, 0.28, 0.27],
  [0.65, 0.59, 0.5, 0.42, 0.35, 0.3, 0.28, 0.26],
  [0.64, 0.58, 0.49, 0.4, 0.34, 0.29, 0.27, 0.25],
  [0.63, 0.56, 0.47, 0.39, 0.33, 0.28, 0.26, 0.24],
];

export default function DemoFieldNdviMap() {
  const [showNdvi, setShowNdvi] = useState(true);
  const bounds = latLngBounds(FIELD_POSITIONS);

  const overlayUrl = useMemo(() => {
    const { width, height, data } = gridToImageData(MOCK_NDVI_GRID);
    if (width === 0 || height === 0) return null;
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    const imageData = new ImageData(width, height);
    imageData.data.set(data);
    ctx.putImageData(imageData, 0, 0);
    return canvas.toDataURL("image/png");
  }, []);

  return (
    <section className="rounded-2xl border border-gray-200 p-6">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-gray-900">Field map + NDVI stress overlay</h3>
        <button
          type="button"
          onClick={() => setShowNdvi((v) => !v)}
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            showNdvi ? "bg-amber-50 text-amber-700" : "bg-gray-100 text-gray-700"
          }`}
        >
          {showNdvi ? "Hide NDVI layer" : "Show NDVI layer"}
        </button>
      </div>
      <p className="mt-1 text-sm text-gray-600">As of Jun 9, 2026 · Demo satellite scan</p>

      <div className="map-inset-controls relative isolate z-0 mt-4 h-72 overflow-hidden rounded-xl">
        <MapContainer bounds={bounds.pad(0.2)} scrollWheelZoom={false} className="h-full w-full">
          <TileLayer attribution={IMAGERY_ATTRIBUTION} url={IMAGERY_URL} />
          <TileLayer url={LABELS_URL} />
          {showNdvi && overlayUrl && <ImageOverlay url={overlayUrl} bounds={bounds} opacity={0.72} />}
          <Polygon
            positions={FIELD_POSITIONS}
            pathOptions={{
              color: showNdvi ? "#ffffff" : "#16a34a",
              weight: showNdvi ? 2 : 3,
              fillOpacity: showNdvi ? 0 : 0.15,
            }}
          />
        </MapContainer>
      </div>

      {showNdvi && (
        <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
          <span className="rounded-md bg-green-600/80 px-2 py-1 text-white">
            &gt; 0.60 Healthy canopy
          </span>
          <span className="rounded-md bg-amber-500/80 px-2 py-1 text-white">
            0.35-0.60 Watch zone
          </span>
          <span className="rounded-md bg-amber-900/80 px-2 py-1 text-white">
            &lt; 0.35 Stressed zone
          </span>
        </div>
      )}
    </section>
  );
}
