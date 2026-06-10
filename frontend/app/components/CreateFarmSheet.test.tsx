import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import CreateFarmSheet from "./CreateFarmSheet";
import { renderWithIntl } from "../test-utils";
import { createFarm } from "../lib/api";

vi.mock("../lib/api", () => ({
  createFarm: vi.fn().mockResolvedValue({ id: 42, name: "New Farm" }),
}));

const mockCreate = vi.mocked(createFarm);

function renderSheet(overrides: Partial<Parameters<typeof CreateFarmSheet>[0]> = {}) {
  const props = {
    open: true,
    onClose: vi.fn(),
    onCreated: vi.fn(),
    ...overrides,
  };
  renderWithIntl(<CreateFarmSheet {...props} />);
  return props;
}

describe("CreateFarmSheet", () => {
  beforeEach(() => {
    mockCreate.mockClear();
  });

  it("renders nothing when closed", () => {
    renderSheet({ open: false });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("requires a name", async () => {
    const user = userEvent.setup();
    renderSheet();
    await user.click(screen.getByRole("button", { name: "Create farm" }));

    expect(await screen.findByText("Name is required")).toBeInTheDocument();
    expect(mockCreate).not.toHaveBeenCalled();
  });

  it("creates with name only, nulling optional fields", async () => {
    const user = userEvent.setup();
    const props = renderSheet();

    await user.type(screen.getByLabelText("Farm name"), "North Field");
    await user.click(screen.getByRole("button", { name: "Create farm" }));

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith({
        name: "North Field",
        location: null,
        crop_type: null,
        planting_date: null,
        soil_type: null,
        acreage_acres: null,
        field_polygon: null,
      });
    });
    expect(props.onCreated).toHaveBeenCalledWith({ id: 42, name: "New Farm" });
  });

  it("passes full details through", async () => {
    const user = userEvent.setup();
    renderSheet();

    await user.type(screen.getByLabelText("Farm name"), "South Field");
    await user.type(screen.getByLabelText("Crop"), "corn");
    await user.selectOptions(screen.getByLabelText("Soil type"), "SandyLoam");
    await user.type(screen.getByLabelText("Acres"), "12.5");
    await user.click(screen.getByRole("button", { name: "Create farm" }));

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "South Field",
          crop_type: "corn",
          soil_type: "SandyLoam",
          acreage_acres: 12.5,
        }),
      );
    });
  });

  it("shows server error and keeps the sheet open", async () => {
    const user = userEvent.setup();
    mockCreate.mockRejectedValueOnce(new Error("boom"));
    const props = renderSheet();

    await user.type(screen.getByLabelText("Farm name"), "X");
    await user.click(screen.getByRole("button", { name: "Create farm" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("boom");
    expect(props.onCreated).not.toHaveBeenCalled();
  });
});
