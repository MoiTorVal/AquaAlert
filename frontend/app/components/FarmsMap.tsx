"use client";

import "leaflet/dist/leaflet.css";
import { divIcon, latLngBounds } from "leaflet";
import { useLocale, useTranslations } from "next-intl";
import { MapContainer, Marker, Polygon, TileLayer } from "react-leaflet";
import { escapeHtml, type FarmMapEntry } from "../lib/farmMap";
import { displayName, formatDate } from "../lib/format";
import { IMAGERY_ATTRIBUTION, IMAGERY_URL, LABELS_URL } from "../lib/mapTiles";

// Leaflet touches `window` at import time, so this component must only be
// loaded with next/dynamic({ ssr: false }).
export default function FarmsMap({
  entries,
  asOf,
  onSelect,
}: {
  entries: FarmMapEntry[];
  asOf: string | null;
  onSelect: (farmId: number) => void;
}) {
  const t = useTranslations("farms");
  const locale = useLocale();
  if (entries.length === 0) {
    return (
      <div className="flex h-[28rem] items-center justify-center rounded-xl border border-gray-200 p-6 text-center text-sm text-gray-500">
        {t("mapEmpty")}
      </div>
    );
  }

  const bounds = latLngBounds(entries.flatMap((e) => e.positions)).pad(0.2);

  return (
    // relative z-0 isolate traps Leaflet's internal z-indexes (up to ~1000)
    // so the map can't paint over modal overlays (same as FieldMap)
    <div className="relative isolate z-0 h-[28rem] overflow-hidden rounded-xl">
      <MapContainer bounds={bounds} className="h-full w-full">
        <TileLayer attribution={IMAGERY_ATTRIBUTION} url={IMAGERY_URL} />
        <TileLayer url={LABELS_URL} />
        {entries.map((entry) => (
          <FarmShape key={entry.farm.id} entry={entry} onSelect={onSelect} />
        ))}
      </MapContainer>
      {asOf && (
        // z-[1000] sits above Leaflet's panes (max ~700) but stays inside
        // this stacking context thanks to `isolate` above
        <span className="pointer-events-none absolute bottom-2 left-2 z-[1000] rounded-md bg-black/60 px-2 py-1 text-xs font-medium text-white">
          {t("mapAsOf", { date: formatDate(asOf, locale) })}
        </span>
      )}
    </div>
  );
}

function FarmShape({
  entry,
  onSelect,
}: {
  entry: FarmMapEntry;
  onSelect: (farmId: number) => void;
}) {
  const { farm, positions, centroid, color } = entry;
  const handlers = { click: () => onSelect(farm.id) };
  // Label pill anchored to the field centroid. divIcon takes an HTML string,
  // so the user-supplied name must be escaped (see farmMap.escapeHtml).
  const label = divIcon({
    className: "farms-map-label",
    iconSize: [0, 0],
    html:
      `<span class="inline-flex -translate-x-1/2 -translate-y-1/2 cursor-pointer items-center gap-1.5 whitespace-nowrap rounded-lg bg-black/70 px-2.5 py-1.5 text-xs font-semibold text-white shadow">` +
      `<span aria-hidden="true" class="h-2 w-2 shrink-0 rounded-full" style="background:${color}"></span>` +
      `${escapeHtml(displayName(farm.name))}</span>`,
  });
  return (
    <>
      <Polygon
        positions={positions}
        pathOptions={{ color, weight: 3, fillColor: color, fillOpacity: 0.15 }}
        eventHandlers={handlers}
      />
      <Marker
        position={centroid}
        icon={label}
        eventHandlers={handlers}
        keyboard
        title={displayName(farm.name)}
      />
    </>
  );
}
