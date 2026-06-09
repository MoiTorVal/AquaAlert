import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import WeeklySavingsChart from "./WeeklySavingsChart";
import { renderWithIntl } from "../test-utils";
import type { WaterSavingsRow } from "../lib/api";

const row = (overrides: Partial<WaterSavingsRow>): WaterSavingsRow => ({
  id: 1,
  farm_id: 1,
  period_start: "2026-06-01",
  period_end: "2026-06-07",
  baseline_gallons: 7000,
  actual_gallons: 4000,
  gallons_saved: 3000,
  kwh_saved: 1.7,
  co2_kg_saved: 0.4,
  computed_at: "2026-06-08T10:00:00Z",
  ...overrides,
});

describe("WeeklySavingsChart", () => {
  it("renders a bar per week plus the cumulative line", () => {
    const { container } = renderWithIntl(
      <WeeklySavingsChart
        rows={[
          row({ id: 1 }),
          row({ id: 2, period_start: "2026-06-08", period_end: "2026-06-14", gallons_saved: 2000 }),
        ]}
      />,
    );
    expect(screen.getByRole("img", { name: /weekly water savings/i })).toBeInTheDocument();
    expect(container.querySelectorAll("rect")).toHaveLength(2);
    expect(container.querySelectorAll("polyline")).toHaveLength(1);
  });

  it("colors overuse weeks red", () => {
    const { container } = renderWithIntl(
      <WeeklySavingsChart rows={[row({ gallons_saved: -500 })]} />,
    );
    expect(container.querySelector("rect")).toHaveClass("fill-red-400");
  });

  it("renders nothing without rows", () => {
    const { container } = renderWithIntl(<WeeklySavingsChart rows={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});
