import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import PendingAssessmentCard from "./PendingAssessmentCard";
import { renderWithIntl } from "../test-utils";
import type { Farm } from "../lib/api";

const farm = {
  id: 5,
  user_id: 1,
  name: "Farm",
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
} satisfies Farm;

const completeFarm = {
  ...farm,
  field_polygon: "POLYGON((0 0,1 0,1 1,0 0))",
  crop_type: "grapes",
  planting_date: "2026-03-25",
  soil_type: "Loam",
} satisfies Farm;

describe("PendingAssessmentCard", () => {
  it("shows the setup checklist with an action when fields are missing", async () => {
    const user = userEvent.setup();
    const onAddDetails = vi.fn();
    renderWithIntl(
      <PendingAssessmentCard farm={farm} onAddDetails={onAddDetails} />,
    );

    expect(
      screen.getByText("Finish setup to start assessments"),
    ).toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: "Add missing details" }),
    );
    expect(onAddDetails).toHaveBeenCalled();
  });

  it("shows the waiting state when setup is complete", () => {
    renderWithIntl(
      <PendingAssessmentCard farm={completeFarm} onAddDetails={vi.fn()} />,
    );

    expect(
      screen.getByText("Waiting on first satellite reading"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Add missing details" }),
    ).not.toBeInTheDocument();
  });
});
