import { describe, expect, it } from "vitest";
import { AWC_IN_PER_FT, gallonsToAcreInches } from "./soil";
import { SOIL_TEXTURES } from "./validators";

describe("AWC_IN_PER_FT", () => {
  it("covers every soil texture the form can submit", () => {
    for (const texture of SOIL_TEXTURES) {
      expect(AWC_IN_PER_FT[texture]).toBeGreaterThan(0);
    }
  });

  it("sands hold less water than loams", () => {
    expect(AWC_IN_PER_FT.Sandy).toBeLessThan(AWC_IN_PER_FT.Loam);
  });
});

describe("gallonsToAcreInches", () => {
  it("converts using 27,154 gal per acre-inch", () => {
    expect(gallonsToAcreInches(27_154)).toBeCloseTo(1.0);
    expect(gallonsToAcreInches(5_000)).toBeCloseTo(0.184, 3);
  });
});
