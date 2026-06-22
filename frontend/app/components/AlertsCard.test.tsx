import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";
import en from "../../messages/en.json";
import AlertsCard from "./AlertsCard";
import { AuthContext } from "../context/AuthContext";
import {
  updateMe,
  type Alert,
  type SatelliteScanSummary,
  type User,
} from "../lib/api";

vi.mock("../lib/api", () => ({
  updateMe: vi.fn(),
}));

const mockUpdateMe = vi.mocked(updateMe);

const baseUser = {
  id: 1,
  email: "farmer@example.com",
  name: "Farmer",
  locale: "en",
  tier: "free",
  is_socially_disadvantaged: null,
  is_beginning_farmer: null,
  phone_number: null,
  sms_alerts_enabled: false,
} satisfies User;

const alert = {
  id: 9,
  farm_id: 5,
  severity: "yellow",
  as_of_date: "2026-06-08",
  days_to_stress: 3,
  channel: "sms",
  sent_at: "2026-06-08T14:00:00Z",
  feedback: "yes",
  feedback_at: "2026-06-08T15:00:00Z",
} satisfies Alert;

const confirmingScan = {
  id: 2,
  farm_id: 5,
  scan_date: "2026-06-07",
  cloud_cover_pct: 3,
  mean_ndvi: 0.31,
  max_ndvi: 0.72,
  min_ndvi: 0.11,
  source: "seed",
  created_at: "2026-06-07T01:00:00Z",
} satisfies SatelliteScanSummary;

function renderCard(
  user: User,
  alerts: Alert[],
  scans: SatelliteScanSummary[] = [],
  setUser = vi.fn(),
) {
  render(
    <NextIntlClientProvider locale="en" messages={en} timeZone="America/Los_Angeles">
      <AuthContext.Provider value={{ user, setUser, isLoading: false }}>
        <AlertsCard alerts={alerts} scans={scans} />
      </AuthContext.Provider>
    </NextIntlClientProvider>,
  );
  return setUser;
}

describe("AlertsCard", () => {
  beforeEach(() => {
    mockUpdateMe.mockReset();
  });

  it("renders alert history with severity and feedback", () => {
    renderCard(baseUser, [alert], [confirmingScan]);
    expect(screen.getByText(/Approaching stress — 3 days left/)).toBeInTheDocument();
    expect(screen.getByText(/NDVI also shows stress/i)).toBeInTheDocument();
    expect(screen.getByText("Confirmed in field")).toBeInTheDocument();
    expect(screen.getByText("Jun 8, 2026")).toBeInTheDocument();
  });

  it("shows NDVI mismatch text when scan looks healthy", () => {
    renderCard(baseUser, [alert], [{ ...confirmingScan, mean_ndvi: 0.74 }]);
    expect(screen.getByText(/NDVI looked healthy/i)).toBeInTheDocument();
  });

  it("shows the empty state without alerts", () => {
    renderCard(baseUser, []);
    expect(screen.getByText(/No alerts yet/)).toBeInTheDocument();
  });

  it("asks for a phone number before enabling SMS without one", async () => {
    const user = userEvent.setup();
    const setUser = renderCard(baseUser, []);
    mockUpdateMe.mockResolvedValue({
      ...baseUser,
      phone_number: "+15551234567",
      sms_alerts_enabled: true,
    });

    await user.click(screen.getByRole("switch"));
    expect(mockUpdateMe).not.toHaveBeenCalled();

    await user.type(screen.getByLabelText("Mobile number"), "+15551234567");
    await user.click(screen.getByRole("button", { name: "Enable SMS alerts" }));

    await waitFor(() =>
      expect(mockUpdateMe).toHaveBeenCalledWith({
        sms_alerts_enabled: true,
        phone_number: "+15551234567",
      }),
    );
    expect(setUser).toHaveBeenCalledWith(
      expect.objectContaining({ sms_alerts_enabled: true }),
    );
  });

  it("disables SMS directly when already enabled", async () => {
    const user = userEvent.setup();
    const enabled = {
      ...baseUser,
      phone_number: "+15551234567",
      sms_alerts_enabled: true,
    } satisfies User;
    renderCard(enabled, []);
    mockUpdateMe.mockResolvedValue({ ...enabled, sms_alerts_enabled: false });

    await user.click(screen.getByRole("switch"));

    await waitFor(() =>
      expect(mockUpdateMe).toHaveBeenCalledWith({ sms_alerts_enabled: false }),
    );
  });

  it("surfaces the API error when saving fails", async () => {
    const user = userEvent.setup();
    const enabled = {
      ...baseUser,
      phone_number: "+15551234567",
      sms_alerts_enabled: true,
    } satisfies User;
    renderCard(enabled, []);
    mockUpdateMe.mockRejectedValue(new Error("Phone number already in use"));

    await user.click(screen.getByRole("switch"));

    expect(
      await screen.findByText("Phone number already in use"),
    ).toBeInTheDocument();
  });
});
