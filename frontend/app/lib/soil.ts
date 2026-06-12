import type { Farm } from "./api";

type SoilTexture = NonNullable<Farm["soil_type"]>;

/** Typical available water capacity by USDA texture class, in inches of
 * water per foot of soil (NRCS Soil Survey Manual field estimates). Display
 * guidance only — the sim uses AquaCrop's own soil hydraulics. */
export const AWC_IN_PER_FT: Record<SoilTexture, number> = {
  Sandy: 0.7,
  LoamySand: 1.1,
  SandyLoam: 1.4,
  Loam: 2.0,
  SiltLoam: 2.2,
  Silt: 2.1,
  SandyClayLoam: 1.6,
  ClayLoam: 1.9,
  SiltyClayLoam: 2.1,
  SandyClay: 1.4,
  SiltyClay: 1.7,
  Clay: 1.6,
};

/** 1 acre-inch = 27,154 US gallons. */
export const GALLONS_PER_ACRE_INCH = 27_154;

export function gallonsToAcreInches(gallons: number): number {
  return gallons / GALLONS_PER_ACRE_INCH;
}
