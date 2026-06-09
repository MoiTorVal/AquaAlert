import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import GlossaryTooltip from "./GlossaryTooltip";
import { renderWithIntl } from "../test-utils";

describe("GlossaryTooltip", () => {
  it("is hidden until clicked, then shows the definition", async () => {
    const user = userEvent.setup();
    renderWithIntl(<GlossaryTooltip term="MAD" />);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "What is MAD?" }));
    expect(screen.getByRole("tooltip")).toHaveTextContent(
      /Management Allowed Depletion/,
    );
  });

  it("toggles closed on second click", async () => {
    const user = userEvent.setup();
    renderWithIntl(<GlossaryTooltip term="ET" />);
    const button = screen.getByRole("button", { name: "What is ET?" });

    await user.click(button);
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
    await user.click(button);
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});
