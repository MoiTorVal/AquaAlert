import { describe, expect, it } from "vitest";

import { gridToImageData } from "./ndvi";

describe("gridToImageData", () => {
  it("maps NDVI bands and transparent nulls", () => {
    const { width, height, data } = gridToImageData([
      [0.7, 0.5, 0.2, null],
    ]);
    expect(width).toBe(4);
    expect(height).toBe(1);
    expect(Array.from(data)).toEqual([
      22, 163, 74, 200, // > 0.6
      245, 158, 11, 200, // 0.35 - 0.6
      146, 64, 14, 200, // < 0.35
      0, 0, 0, 0, // null transparent
    ]);
  });

  it("pads ragged rows with transparent cells", () => {
    const { width, height, data } = gridToImageData([[0.61], [0.34, 0.36]]);
    expect(width).toBe(2);
    expect(height).toBe(2);
    // row0 col1 should be transparent padding
    expect(Array.from(data.slice(4, 8))).toEqual([0, 0, 0, 0]);
  });
});
