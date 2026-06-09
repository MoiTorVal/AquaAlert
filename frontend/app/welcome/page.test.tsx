import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import WelcomePage from "./page";
import { renderWithIntl } from "../test-utils";
import { updateMe } from "../lib/api";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));
vi.mock("../lib/api", () => ({
  updateMe: vi.fn().mockResolvedValue({}),
}));

const mockUpdate = vi.mocked(updateMe);

describe("WelcomePage equity self-ID", () => {
  beforeEach(() => {
    push.mockClear();
    mockUpdate.mockClear();
  });

  it("skip never calls the API and goes to farms", async () => {
    const user = userEvent.setup();
    renderWithIntl(<WelcomePage />);
    await user.click(screen.getByRole("button", { name: "Skip" }));

    expect(mockUpdate).not.toHaveBeenCalled();
    expect(push).toHaveBeenCalledWith("/farms");
  });

  it("saves explicit answers", async () => {
    const user = userEvent.setup();
    renderWithIntl(<WelcomePage />);

    const yesButtons = screen.getAllByRole("button", { name: "Yes" });
    const noButtons = screen.getAllByRole("button", { name: "No" });
    await user.click(yesButtons[0]!);
    await user.click(noButtons[1]!);
    await user.click(screen.getByRole("button", { name: "Save answers" }));

    await waitFor(() =>
      expect(mockUpdate).toHaveBeenCalledWith({
        is_socially_disadvantaged: true,
        is_beginning_farmer: false,
      }),
    );
    expect(push).toHaveBeenCalledWith("/farms");
  });

  it("prefer-not-to-say stores null", async () => {
    const user = userEvent.setup();
    renderWithIntl(<WelcomePage />);
    await user.click(screen.getByRole("button", { name: "Save answers" }));

    await waitFor(() =>
      expect(mockUpdate).toHaveBeenCalledWith({
        is_socially_disadvantaged: null,
        is_beginning_farmer: null,
      }),
    );
  });
});
