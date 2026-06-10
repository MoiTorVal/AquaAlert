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
