import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import FarmSetupCard from "./FarmSetupCard";
import { renderWithIntl } from "../test-utils";
import { createBaselineIrrigation, updateFarm, type Farm } from "../lib/api";

vi.mock("../lib/api", () => ({
  createBaselineIrrigation: vi.fn().mockResolvedValue({}),
  updateFarm: vi.fn().mockResolvedValue({}),
}));

const mockBaseline = vi.mocked(createBaselineIrrigation);
const mockUpdate = vi.mocked(updateFarm);

const farm = {
  id: 5,
  user_id: 1,
  name: "Farm",
  location: null,
  area_hectares: null,
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

describe("FarmSetupCard", () => {
  beforeEach(() => {
    window.localStorage.removeItem("farm-setup-dismissed-5");
    mockBaseline.mockClear();
    mockUpdate.mockClear();
  });

  it("hides when baseline and pump are already set", () => {
    renderWithIntl(
      <FarmSetupCard
        farm={{ ...farm, pump_hp: 25, pump_lift_ft: 100 }}
        hasBaseline={true}
        onChanged={vi.fn()}
      />,
    );
    expect(screen.queryByTestId("farm-setup-card")).not.toBeInTheDocument();
  });

  it("saves baseline and pump profile", async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    renderWithIntl(
      <FarmSetupCard farm={farm} hasBaseline={false} onChanged={onChanged} />,
    );

    await user.type(
      screen.getByLabelText(/Gallons per week/),
      "7000",
    );
    await user.type(screen.getByLabelText("Pump lift (feet)"), "120");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(onChanged).toHaveBeenCalled());
    expect(mockBaseline).toHaveBeenCalledWith(5, 7000);
    expect(mockUpdate).toHaveBeenCalledWith(
      5,
      expect.objectContaining({ pump_lift_ft: 120 }),
    );
  });

  it("skip dismisses and persists in localStorage", async () => {
    const user = userEvent.setup();
    renderWithIntl(
      <FarmSetupCard farm={farm} hasBaseline={false} onChanged={vi.fn()} />,
    );
    await user.click(screen.getByRole("button", { name: "Skip for now" }));

    expect(screen.queryByTestId("farm-setup-card")).not.toBeInTheDocument();
    expect(window.localStorage.getItem("farm-setup-dismissed-5")).toBe("1");
  });

  it("stays hidden on later renders after dismissal", () => {
    window.localStorage.setItem("farm-setup-dismissed-5", "1");
    renderWithIntl(
      <FarmSetupCard farm={farm} hasBaseline={false} onChanged={vi.fn()} />,
    );
    expect(screen.queryByTestId("farm-setup-card")).not.toBeInTheDocument();
  });
});
