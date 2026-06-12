import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import SavingsCard from "./SavingsCard";
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

describe("SavingsCard", () => {
  it("sums season totals and shows latest period as as-of date", () => {
    renderWithIntl(
      <SavingsCard
        rows={[
          row({ id: 1 }),
          row({
            id: 2,
            period_start: "2026-06-08",
            period_end: "2026-06-14",
            gallons_saved: 2000,
            kwh_saved: 1.1,
            co2_kg_saved: 0.3,
          }),
        ]}
      />,
    );
    expect(screen.getByText("5,000 gal saved")).toBeInTheDocument();
    expect(screen.getByText(/2\.8 kWh .* 0\.7 kg CO₂/)).toBeInTheDocument();
    expect(screen.getByText("As of Jun 14, 2026")).toBeInTheDocument();
  });

  it("shows empty state without rows", () => {
    renderWithIntl(<SavingsCard rows={[]} />);
    expect(screen.getByText(/No savings data yet/)).toBeInTheDocument();
  });
});
