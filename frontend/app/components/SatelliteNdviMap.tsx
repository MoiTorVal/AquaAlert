"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useMemo, useState } from "react";
import { latLngBounds } from "leaflet";
import { ImageOverlay, MapContainer, Polygon, TileLayer } from "react-leaflet";
import { useLocale, useTranslations } from "next-intl";

import {
  getSatelliteScan,
  type SatelliteScan,
  type SatelliteScanSummary,
} from "../lib/api";
import { formatDate } from "../lib/format";
import { IMAGERY_ATTRIBUTION, IMAGERY_URL, LABELS_URL } from "../lib/mapTiles";
import { gridToImageData } from "../lib/ndvi";
import { parseWktPolygon } from "../lib/wkt";

export default function SatelliteNdviMap({
  farmId,
  wkt,
  scans,
}: {
  farmId: number;
  wkt: string;
  scans: SatelliteScanSummary[];
}) {
  const t = useTranslations("farmDetail");
  const locale = useLocale();
  const positions = parseWktPolygon(wkt);
  const [index, setIndex] = useState(0);
  // Grids are fetched lazily per timeline position and cached; null marks a
  // failed fetch so we don't retry it on every render.
  const [details, setDetails] = useState<
    Record<number, SatelliteScan | null>
  >({});
  const scan = scans[index] ?? null;
  const detail = scan != null ? details[scan.id] : undefined;

  useEffect(() => {
    if (scan == null || details[scan.id] !== undefined) return;
    let active = true;
    const scanId = scan.id;
    getSatelliteScan(farmId, scanId).then(
      (full) => {
        if (active) setDetails((d) => ({ ...d, [scanId]: full }));
      },
      () => {
        if (active) setDetails((d) => ({ ...d, [scanId]: null }));
      },
    );
    return () => {
      active = false;
    };
  }, [farmId, scan, details]);

  const overlayUrl = useMemo(() => {
    if (detail?.ndvi_grid == null) return null;
    const { width, height, data } = gridToImageData(detail.ndvi_grid);
    if (width === 0 || height === 0) return null;
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    if (context == null) return null;
    const imageData = new ImageData(width, height);
    imageData.data.set(data);
    context.putImageData(imageData, 0, 0);
    return canvas.toDataURL("image/png");
  }, [detail]);

  if (!positions || scan == null) return null;

  const polygonBounds = latLngBounds(positions);
  // Real scans carry the raster window's bounds; seeded grids are drawn over
  // the field, so the polygon bbox is the right footprint for them.
  const overlayBounds =
    detail?.ndvi_grid_bounds != null
      ? latLngBounds(detail.ndvi_grid_bounds)
      : polygonBounds;

  return (
    <section className="rounded-2xl border border-gray-200 p-6">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-base font-semibold">{t("ndviTitle")}</h3>
        {scan.source === "seed" && (
          <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700">
            {t("ndviDemoBadge")}
          </span>
        )}
      </div>
      <p className="mt-1 text-sm text-gray-600">
        {t("ndviAsOf", { date: formatDate(scan.scan_date, locale) })}
      </p>
      <p className="mt-1 text-xs text-gray-500">{t("ndviHelper")}</p>

      <div className="relative isolate z-0 mt-4 h-72 overflow-hidden rounded-xl">
        <MapContainer
          bounds={polygonBounds.pad(0.2)}
          scrollWheelZoom={false}
          className="h-full w-full"
        >
          <TileLayer attribution={IMAGERY_ATTRIBUTION} url={IMAGERY_URL} />
          <TileLayer url={LABELS_URL} />
          {overlayUrl && (
            <ImageOverlay
              url={overlayUrl}
              bounds={overlayBounds}
              opacity={0.72}
            />
          )}
          <Polygon
            positions={positions}
            pathOptions={{ color: "#ffffff", weight: 2, fillOpacity: 0 }}
          />
        </MapContainer>
      </div>

      {scans.length > 1 && (
        <div className="mt-4">
          <label className="mb-1 block text-xs text-gray-600" htmlFor="ndvi-timeline">
            {t("ndviTimeline")}
          </label>
          <input
            id="ndvi-timeline"
            type="range"
            min={0}
            max={scans.length - 1}
            value={index}
            onChange={(e) => setIndex(Number(e.target.value))}
            className="w-full"
          />
        </div>
      )}

      <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
        <span className="rounded-md bg-green-600/80 px-2 py-1 text-white">
          {t("ndviLegendHigh")}
        </span>
        <span className="rounded-md bg-amber-500/80 px-2 py-1 text-white">
          {t("ndviLegendMid")}
        </span>
        <span className="rounded-md bg-amber-900/80 px-2 py-1 text-white">
          {t("ndviLegendLow")}
        </span>
      </div>
    </section>
  );
}
