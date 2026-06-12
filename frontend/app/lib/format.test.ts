import { describe, expect, it } from "vitest";
import { displayName, formatDate, isoAddDays } from "./format";

describe("isoAddDays", () => {
  it("adds and subtracts days", () => {
    expect(isoAddDays("2026-06-10", -6)).toBe("2026-06-04");
    expect(isoAddDays("2026-06-10", 1)).toBe("2026-06-11");
  });

  it("crosses month and year boundaries", () => {
    expect(isoAddDays("2026-03-01", -1)).toBe("2026-02-28");
    expect(isoAddDays("2026-01-01", -1)).toBe("2025-12-31");
  });
});

describe("formatDate", () => {
  it("formats ISO dates for display", () => {
    expect(formatDate("2026-03-25", "en")).toBe("Mar 25, 2026");
  });

  it("does not shift the date across timezones", () => {
    // Date-only strings must render the same day everywhere.
    expect(formatDate("2026-01-01", "en")).toBe("Jan 1, 2026");
    expect(formatDate("2026-12-31", "en")).toBe("Dec 31, 2026");
  });

  it("localizes by locale", () => {
    expect(formatDate("2026-03-25", "es")).toMatch(/mar/i);
  });

  it("handles null and garbage", () => {
    expect(formatDate(null, "en")).toBe("—");
    expect(formatDate("not-a-date", "en")).toBe("not-a-date");
  });
});

describe("displayName", () => {
  it("capitalizes each word", () => {
    expect(displayName("shmoi's farms")).toBe("Shmoi's Farms");
    expect(displayName("porterville")).toBe("Porterville");
  });

  it("leaves existing capitals alone", () => {
    expect(displayName("USDA test Plot")).toBe("USDA Test Plot");
  });

  it("handles null", () => {
    expect(displayName(null)).toBe("—");
  });
});
