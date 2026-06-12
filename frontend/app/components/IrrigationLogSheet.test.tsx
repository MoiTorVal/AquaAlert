import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import IrrigationLogSheet from "./IrrigationLogSheet";
import { renderWithIntl } from "../test-utils";
import {
  logIrrigationEvent,
  updateIrrigationEvent,
  type IrrigationEvent,
} from "../lib/api";
import { gallonsFromForm } from "../lib/validators";

vi.mock("../lib/api", () => ({
  logIrrigationEvent: vi.fn().mockResolvedValue({}),
  updateIrrigationEvent: vi.fn().mockResolvedValue({}),
}));

const mockLog = vi.mocked(logIrrigationEvent);
const mockUpdate = vi.mocked(updateIrrigationEvent);

const runtimeEvent = {
  id: 42,
  farm_id: 7,
  event_date: "2026-06-12",
  gallons_applied: 30000,
  hours_run: 50,
  pump_gpm: 10,
  source: "user_log",
  logged_at: "2026-06-12T16:00:00Z",
} satisfies IrrigationEvent;

function renderSheet(overrides: Partial<Parameters<typeof IrrigationLogSheet>[0]> = {}) {
  const props = {
    farmId: 7,
    open: true,
    onClose: vi.fn(),
    onLogged: vi.fn(),
    ...overrides,
  };
  renderWithIntl(<IrrigationLogSheet {...props} />);
  return props;
}

describe("IrrigationLogSheet", () => {
  beforeEach(() => {
    mockLog.mockClear();
    mockUpdate.mockClear();
  });

  it("renders nothing when closed", () => {
    renderSheet({ open: false });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("defaults the date to today", () => {
    renderSheet();
    const today = new Date().toISOString().slice(0, 10);
    expect(screen.getByLabelText("Date")).toHaveValue(today);
  });

  it("posts gallons directly and fires callbacks", async () => {
    const user = userEvent.setup();
    const props = renderSheet();

    await user.type(screen.getByLabelText("Gallons applied"), "2500");
    await user.click(screen.getByRole("button", { name: "Save Irrigation" }));

    await waitFor(() => {
      expect(mockLog).toHaveBeenCalledWith(7, {
        event_date: new Date().toISOString().slice(0, 10),
        gallons_applied: 2500,
      });
    });
    expect(props.onLogged).toHaveBeenCalled();
    expect(props.onClose).toHaveBeenCalled();
  });

  it("converts pump runtime to gallons", async () => {
    const user = userEvent.setup();
    renderSheet();

    await user.click(screen.getByLabelText("Pump runtime"));
    await user.type(screen.getByLabelText("Hours run"), "2");
    await user.type(screen.getByLabelText("Pump flow (GPM)"), "300");
    await user.click(screen.getByRole("button", { name: "Save Irrigation" }));

    await waitFor(() => {
      // 2 h x 300 gal/min x 60 min/h
      expect(mockLog).toHaveBeenCalledWith(
        7,
        expect.objectContaining({ gallons_applied: 36000 }),
      );
    });
  });

  it("blocks submit when gallons missing", async () => {
    const user = userEvent.setup();
    renderSheet();

    await user.click(screen.getByRole("button", { name: "Save Irrigation" }));

    expect(await screen.findByText("Gallons is required")).toBeInTheDocument();
    expect(mockLog).not.toHaveBeenCalled();
  });

  it("prefills the entry being edited in its original mode", () => {
    renderSheet({ event: runtimeEvent });

    expect(screen.getByText("Edit Irrigation")).toBeInTheDocument();
    expect(screen.getByLabelText("Date")).toHaveValue("2026-06-12");
    expect(screen.getByLabelText("Pump runtime")).toBeChecked();
    expect(screen.getByLabelText("Hours run")).toHaveValue(50);
    expect(screen.getByLabelText("Pump flow (GPM)")).toHaveValue(10);
  });

  it("updates instead of creating, clearing runtime on a gallons correction", async () => {
    const user = userEvent.setup();
    const props = renderSheet({ event: runtimeEvent });

    await user.click(screen.getByLabelText("Gallons"));
    await user.type(screen.getByLabelText("Gallons applied"), "700");
    await user.click(screen.getByRole("button", { name: "Save Changes" }));

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith(7, 42, {
        event_date: "2026-06-12",
        gallons_applied: 700,
      });
    });
    expect(mockLog).not.toHaveBeenCalled();
    expect(props.onLogged).toHaveBeenCalled();
    expect(props.onClose).toHaveBeenCalled();
  });

  it("shows server error and stays open on API failure", async () => {
    const user = userEvent.setup();
    mockLog.mockRejectedValueOnce(new Error("quota reached"));
    const props = renderSheet();

    await user.type(screen.getByLabelText("Gallons applied"), "100");
    await user.click(screen.getByRole("button", { name: "Save Irrigation" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("quota reached");
    expect(props.onClose).not.toHaveBeenCalled();
  });
});

describe("gallonsFromForm", () => {
  it("passes gallons through unchanged", () => {
    expect(
      gallonsFromForm({ event_date: "2026-06-09", mode: "gallons", gallons: "1234" }),
    ).toBe(1234);
  });

  it("rounds runtime conversion", () => {
    expect(
      gallonsFromForm({ event_date: "2026-06-09", mode: "runtime", hours: "1.5", gpm: "333" }),
    ).toBe(29970);
  });
});
