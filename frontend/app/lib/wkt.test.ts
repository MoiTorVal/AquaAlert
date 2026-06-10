import { describe, expect, it } from "vitest";
import { parseWktPolygon, toWktPolygon } from "./wkt";

describe("parseWktPolygon", () => {
  it("parses a WKT polygon into [lat, lng] pairs", () => {
    const wkt =
      "POLYGON ((-120.5 36.7, -120.4 36.7, -120.4 36.8, -120.5 36.7))";
    expect(parseWktPolygon(wkt)).toEqual([
      [36.7, -120.5],
      [36.7, -120.4],
      [36.8, -120.4],
      [36.7, -120.5],
    ]);
  });

  it("accepts no space after POLYGON", () => {
    const wkt = "POLYGON((-1 2, -3 4, -5 6, -1 2))";
    expect(parseWktPolygon(wkt)).toHaveLength(4);
  });

  it("returns null for non-polygon WKT", () => {
    expect(parseWktPolygon("POINT (-120.5 36.7)")).toBeNull();
  });

  it("returns null for malformed coordinates", () => {
    expect(parseWktPolygon("POLYGON ((-120.5 abc, -120.4 36.7))")).toBeNull();
  });

  it("returns null for a ring with fewer than 4 points", () => {
    expect(parseWktPolygon("POLYGON ((-1 2, -3 4, -1 2))")).toBeNull();
  });
});

describe("toWktPolygon", () => {
  it("closes an open ring and emits lon-lat order", () => {
    const wkt = toWktPolygon([
      [36.7, -120.5],
      [36.7, -120.4],
      [36.8, -120.4],
    ]);
    expect(wkt).toBe(
      "POLYGON ((-120.5 36.7, -120.4 36.7, -120.4 36.8, -120.5 36.7))",
    );
  });

  it("keeps an already-closed ring closed", () => {
    const wkt = toWktPolygon([
      [36.7, -120.5],
      [36.7, -120.4],
      [36.8, -120.4],
      [36.7, -120.5],
    ]);
    expect(wkt).toBe(
      "POLYGON ((-120.5 36.7, -120.4 36.7, -120.4 36.8, -120.5 36.7))",
    );
  });

  it("returns null for fewer than 3 points", () => {
    expect(
      toWktPolygon([
        [36.7, -120.5],
        [36.7, -120.4],
      ]),
    ).toBeNull();
  });

  it("round-trips through parseWktPolygon", () => {
    const ring: [number, number][] = [
      [36.7, -120.5],
      [36.7, -120.4],
      [36.8, -120.4],
      [36.7, -120.5],
    ];
    expect(parseWktPolygon(toWktPolygon(ring)!)).toEqual(ring);
  });
});
