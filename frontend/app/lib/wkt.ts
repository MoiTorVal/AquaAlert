// Backend serializes Farm.field_polygon as WKT, e.g.
// "POLYGON ((-120.5 36.7, -120.4 36.7, -120.4 36.8, -120.5 36.7))".
// WKT order is lon lat; Leaflet wants [lat, lng].
export function parseWktPolygon(wkt: string): [number, number][] | null {
  const ring = wkt.match(/^POLYGON\s*\(\(([^)]+)\)/i)?.[1];
  if (!ring) return null;
  const coords: [number, number][] = [];
  for (const pair of ring.split(",")) {
    const [lon, lat, ...rest] = pair.trim().split(/\s+/).map(Number);
    if (lon === undefined || lat === undefined || rest.length > 0) return null;
    if (Number.isNaN(lon) || Number.isNaN(lat)) return null;
    coords.push([lat, lon]);
  }
  return coords.length >= 4 ? coords : null;
}

// Inverse of parseWktPolygon: Leaflet [lat, lng] ring (open or closed)
// → WKT POLYGON with a closed lon-lat ring, as the backend expects.
export function toWktPolygon(latLngs: [number, number][]): string | null {
  if (latLngs.length < 3) return null;
  const ring = [...latLngs];
  const first = ring[0];
  const last = ring[ring.length - 1];
  if (!first || !last) return null;
  if (first[0] !== last[0] || first[1] !== last[1]) ring.push(first);
  const pairs = ring.map(([lat, lng]) => `${lng} ${lat}`).join(", ");
  return `POLYGON ((${pairs}))`;
}
