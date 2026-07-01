// Pure data prep for the all-farms map view: WKT → Leaflet rings, severity
// colors, label placement. Kept Leaflet-free so it can be unit tested.
import type { Farm, WaterStress } from "./api";
import { parseWktPolygon } from "./wkt";

export type Severity = NonNullable<WaterStress["severity"]>;

// Matches the traffic-light palette used across the app (STATUS_STYLES on the
// farms list, TrafficLightCard). Gray = no assessment yet.
export const SEVERITY_COLORS: Record<Severity | "none", string> = {
  green: "#16a34a",
  yellow: "#f59e0b",
  red: "#dc2626",
  none: "#9ca3af",
};

export function severityColor(severity: Severity | null | undefined): string {
  return SEVERITY_COLORS[severity ?? "none"];
}

export type FarmMapEntry = {
  farm: Farm;
  positions: [number, number][];
  centroid: [number, number];
  severity: Severity | null;
  color: string;
};

/** Vertex average — good enough to anchor a label on field-sized polygons.
 * Drops the closing vertex so it isn't double-counted. */
export function polygonCentroid(
  positions: [number, number][],
): [number, number] {
  const first = positions[0];
  const last = positions[positions.length - 1];
  if (!first || !last) return [0, 0];
  const ring =
    positions.length > 1 && first[0] === last[0] && first[1] === last[1]
      ? positions.slice(0, -1)
      : positions;
  let lat = 0;
  let lng = 0;
  for (const [a, b] of ring) {
    lat += a;
    lng += b;
  }
  return [lat / ring.length, lng / ring.length];
}

/** Farms without a parseable polygon are skipped — the map can only show
 * drawn boundaries; the page reports how many were left out. */
export function buildFarmMapEntries(
  farms: Farm[],
  stressMap: Record<number, WaterStress | null>,
): FarmMapEntry[] {
  const entries: FarmMapEntry[] = [];
  for (const farm of farms) {
    if (!farm.field_polygon) continue;
    const positions = parseWktPolygon(farm.field_polygon);
    if (!positions) continue;
    const severity = stressMap[farm.id]?.severity ?? null;
    entries.push({
      farm,
      positions,
      centroid: polygonCentroid(positions),
      severity,
      color: severityColor(severity),
    });
  }
  return entries;
}

/** Newest assessment date across the mapped farms — the map's "as of" stamp.
 * ISO date strings compare correctly as strings. */
export function latestAsOf(
  entries: FarmMapEntry[],
  stressMap: Record<number, WaterStress | null>,
): string | null {
  let latest: string | null = null;
  for (const { farm } of entries) {
    const asOf = stressMap[farm.id]?.as_of_date;
    if (asOf && (latest === null || asOf > latest)) latest = asOf;
  }
  return latest;
}

/** Farm names are user input and get injected into a Leaflet divIcon HTML
 * string — they must be escaped or a farm named `<img onerror=...>` is XSS. */
export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
