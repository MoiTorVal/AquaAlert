import { describe, expect, it } from "vitest";
import type { Farm, WaterStress } from "./api";
import {
  buildFarmMapEntries,
  escapeHtml,
  latestAsOf,
  polygonCentroid,
  severityColor,
  SEVERITY_COLORS,
} from "./farmMap";

const farm = (overrides: Partial<Farm>): Farm => ({
  id: 1,
  name: "test farm",
  location: null,
  crop_type: null,
  soil_type: null,
  root_depth_cm: null,
  growth_stage: null,
  planting_date: null,
  field_capacity_pct: null,
  wilting_point_pct: null,
  field_polygon: null,
  harvest_date: null,
  acreage_acres: null,
  pump_hp: null,
  pump_lift_ft: null,
  water_source: null,
  created_at: null,
  ...overrides,
});

const stress = (overrides: Partial<WaterStress>): WaterStress => ({
  id: 1,
  farm_id: 1,
  as_of_date: "2026-06-05",
  depletion_mm: null,
  root_zone_moisture_pct: null,
  severity: "green",
  days_to_stress: null,
  paw_mm: null,
  raw_threshold_mm: null,
  run_date: null,
  et_latest_date: null,
  et_is_stale: false,
  ...overrides,
});

const SQUARE = "POLYGON ((-120.5 36.7, -120.4 36.7, -120.4 36.8, -120.5 36.8, -120.5 36.7))";

describe("severityColor", () => {
  it("maps each severity to its palette color", () => {
    expect(severityColor("green")).toBe(SEVERITY_COLORS.green);
    expect(severityColor("yellow")).toBe(SEVERITY_COLORS.yellow);
    expect(severityColor("red")).toBe(SEVERITY_COLORS.red);
  });

  it("falls back to gray when there is no assessment", () => {
    expect(severityColor(null)).toBe(SEVERITY_COLORS.none);
    expect(severityColor(undefined)).toBe(SEVERITY_COLORS.none);
  });
});

describe("polygonCentroid", () => {
  it("averages vertices without double-counting the closing point", () => {
    const closed: [number, number][] = [
      [0, 0],
      [0, 10],
      [10, 10],
      [10, 0],
      [0, 0],
    ];
    expect(polygonCentroid(closed)).toEqual([5, 5]);
  });

  it("handles an open ring", () => {
    const open: [number, number][] = [
      [0, 0],
      [0, 10],
      [10, 10],
      [10, 0],
    ];
    expect(polygonCentroid(open)).toEqual([5, 5]);
  });

  it("returns [0, 0] for an empty ring", () => {
    expect(polygonCentroid([])).toEqual([0, 0]);
  });
});

describe("buildFarmMapEntries", () => {
  it("builds entries with severity color and centroid", () => {
    const f = farm({ id: 7, field_polygon: SQUARE });
    const entries = buildFarmMapEntries([f], {
      7: stress({ farm_id: 7, severity: "red" }),
    });
    expect(entries).toHaveLength(1);
    expect(entries[0]?.severity).toBe("red");
    expect(entries[0]?.color).toBe(SEVERITY_COLORS.red);
    expect(entries[0]?.centroid[0]).toBeCloseTo(36.75);
    expect(entries[0]?.centroid[1]).toBeCloseTo(-120.45);
  });

  it("skips farms without a polygon or with unparseable WKT", () => {
    const entries = buildFarmMapEntries(
      [
        farm({ id: 1, field_polygon: null }),
        farm({ id: 2, field_polygon: "not wkt" }),
        farm({ id: 3, field_polygon: SQUARE }),
      ],
      {},
    );
    expect(entries.map((e) => e.farm.id)).toEqual([3]);
  });

  it("colors farms gray while stress is loading or absent", () => {
    const entries = buildFarmMapEntries(
      [farm({ id: 1, field_polygon: SQUARE })],
      { 1: null },
    );
    expect(entries[0]?.severity).toBeNull();
    expect(entries[0]?.color).toBe(SEVERITY_COLORS.none);
  });
});

describe("latestAsOf", () => {
  it("returns the newest as_of_date across mapped farms", () => {
    const farms = [
      farm({ id: 1, field_polygon: SQUARE }),
      farm({ id: 2, field_polygon: SQUARE }),
    ];
    const stressMap = {
      1: stress({ farm_id: 1, as_of_date: "2026-06-01" }),
      2: stress({ farm_id: 2, as_of_date: "2026-06-09" }),
    };
    const entries = buildFarmMapEntries(farms, stressMap);
    expect(latestAsOf(entries, stressMap)).toBe("2026-06-09");
  });

  it("returns null when no mapped farm has an assessment", () => {
    const farms = [farm({ id: 1, field_polygon: SQUARE })];
    const entries = buildFarmMapEntries(farms, {});
    expect(latestAsOf(entries, {})).toBeNull();
  });

  it("ignores assessments of farms that are not on the map", () => {
    const farms = [farm({ id: 1, field_polygon: null })];
    const stressMap = { 1: stress({ as_of_date: "2026-06-09" }) };
    const entries = buildFarmMapEntries(farms, stressMap);
    expect(latestAsOf(entries, stressMap)).toBeNull();
  });
});

describe("escapeHtml", () => {
  it("escapes HTML-significant characters", () => {
    expect(escapeHtml(`<img src=x onerror="pwn('&')">`)).toBe(
      "&lt;img src=x onerror=&quot;pwn(&#39;&amp;&#39;)&quot;&gt;",
    );
  });

  it("leaves plain names untouched", () => {
    expect(escapeHtml("North Field 2")).toBe("North Field 2");
  });
});
