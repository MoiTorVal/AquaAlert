import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import TrafficLightCard from "./TrafficLightCard";
import { renderWithIntl } from "../test-utils";
import type { WaterStress } from "../lib/api";

const base: WaterStress = {
  id: 1,
  farm_id: 1,
  as_of_date: "2026-06-05",
  depletion_mm: 33.4,
  root_zone_moisture_pct: 69.7,
  severity: "green",
  days_to_stress: 41,
  paw_mm: 77.0,
  raw_threshold_mm: 76.2,
  run_date: null,
  et_latest_date: "2026-06-05",
  et_is_stale: false,
};

describe("TrafficLightCard", () => {
  it("shows healthy state with days remaining", () => {
    renderWithIntl(<TrafficLightCard stress={base} />);
    expect(screen.getByText("Healthy")).toBeInTheDocument();
    expect(
      screen.getByText(/No stress expected for roughly 41 days/),
    ).toBeInTheDocument();
    expect(screen.getByText(/As of Jun 5, 2026/)).toBeInTheDocument();
  });

  it("shows yellow warning with countdown", () => {
    renderWithIntl(
      <TrafficLightCard
        stress={{ ...base, severity: "yellow", days_to_stress: 2 }}
      />,
    );
    expect(screen.getByText("Approaching stress")).toBeInTheDocument();
    expect(
      screen.getByText(/Approaching stress — about 2 days of water left/),
    ).toBeInTheDocument();
  });

  it("shows red stress state", () => {
    renderWithIntl(
      <TrafficLightCard
        stress={{ ...base, severity: "red", days_to_stress: 0 }}
      />,
    );
    expect(screen.getByText("Water stress")).toBeInTheDocument();
    expect(screen.getByText(/Irrigation is recommended/)).toBeInTheDocument();
  });

  it("shows stale-data banner when ET is delayed", () => {
    renderWithIntl(<TrafficLightCard stress={{ ...base, et_is_stale: true }} />);
    expect(screen.getByRole("status")).toHaveTextContent(
      /Satellite data is delayed/,
    );
  });

  it("handles missing severity", () => {
    renderWithIntl(
      <TrafficLightCard
        stress={{ ...base, severity: null, days_to_stress: null }}
      />,
    );
    expect(screen.getByText("No assessment yet")).toBeInTheDocument();
  });
});

describe("plural handling", () => {
  it("uses singular day", () => {
    renderWithIntl(
      <TrafficLightCard
        stress={{ ...base, severity: "yellow", days_to_stress: 1 }}
      />,
    );
    expect(
      screen.getByText(/about 1 day of water left/),
    ).toBeInTheDocument();
  });
});
