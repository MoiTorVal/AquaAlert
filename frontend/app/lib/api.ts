import { z } from "zod";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;
if (!API_BASE) {
  throw new Error("NEXT_PUBLIC_API_BASE_URL is not set");
}

export interface SignupRequest {
  name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export const LocaleSchema = z.enum(["en", "es"]);
export const TierSchema = z.enum(["free", "paid"]);

export const UserSchema = z.object({
  id: z.number(),
  email: z.string(),
  name: z.string().nullable(),
  locale: LocaleSchema,
  tier: TierSchema,
  is_socially_disadvantaged: z.boolean().nullable(),
  is_beginning_farmer: z.boolean().nullable(),
});

export const AuthResponseSchema = z.object({
  message: z.string(),
  user: UserSchema,
});

export const MessageResponseSchema = z.object({
  message: z.string(),
});

export const SoilTextureSchema = z.enum([
  "Sandy",
  "LoamySand",
  "SandyLoam",
  "Loam",
  "SiltLoam",
  "Silt",
  "SandyClayLoam",
  "ClayLoam",
  "SiltyClayLoam",
  "SandyClay",
  "SiltyClay",
  "Clay",
]);

export const WaterSourceSchema = z.enum(["well", "canal", "surface"]);

export const FarmSchema = z.object({
  id: z.number(),
  user_id: z.number(),
  name: z.string(),
  location: z.string().nullable(),
  crop_type: z.string().nullable(),
  soil_type: SoilTextureSchema.nullable(),
  root_depth_cm: z.number().nullable(),
  growth_stage: z.string().nullable(),
  planting_date: z.string().nullable(),
  field_capacity_pct: z.number().nullable(),
  wilting_point_pct: z.number().nullable(),
  field_polygon: z.string().nullable(),
  harvest_date: z.string().nullable(),
  acreage_acres: z.number().nullable(),
  pump_hp: z.number().nullable(),
  pump_lift_ft: z.number().nullable(),
  water_source: WaterSourceSchema.nullable(),
  created_at: z.string().nullable(),
});

export const FarmsListSchema = z.array(FarmSchema);

export const StressSeveritySchema = z.enum(["green", "yellow", "red"]);

export const WaterStressSchema = z.object({
  id: z.number(),
  farm_id: z.number(),
  as_of_date: z.string(),
  depletion_mm: z.coerce.number().nullable(),
  root_zone_moisture_pct: z.coerce.number().nullable(),
  severity: StressSeveritySchema.nullable(),
  days_to_stress: z.number().nullable(),
  paw_mm: z.coerce.number().nullable(),
  raw_threshold_mm: z.coerce.number().nullable(),
  run_date: z.string().nullable(),
  et_latest_date: z.string().nullable(),
  et_is_stale: z.boolean(),
});

export const WaterSavingsRowSchema = z.object({
  id: z.number(),
  farm_id: z.number(),
  period_start: z.string(),
  period_end: z.string(),
  baseline_gallons: z.coerce.number(),
  actual_gallons: z.coerce.number(),
  gallons_saved: z.coerce.number(),
  kwh_saved: z.coerce.number(),
  co2_kg_saved: z.coerce.number(),
  computed_at: z.string(),
});

export const PaginatedWaterSavingsSchema = z.object({
  total: z.number(),
  skip: z.number(),
  limit: z.number(),
  results: z.array(WaterSavingsRowSchema),
});

export const IrrigationEventSchema = z.object({
  id: z.number(),
  farm_id: z.number(),
  event_date: z.string(),
  gallons_applied: z.coerce.number(),
  source: z.enum(["user_log", "estimated"]),
  logged_at: z.string(),
});

export const BaselineIrrigationSchema = z.object({
  id: z.number(),
  farm_id: z.number(),
  gallons_per_week_estimate: z.coerce.number(),
  created_at: z.string(),
});

export const PaginatedBaselineSchema = z.object({
  total: z.number(),
  skip: z.number(),
  limit: z.number(),
  results: z.array(BaselineIrrigationSchema),
});

export type BaselineIrrigation = z.infer<typeof BaselineIrrigationSchema>;
export type User = z.infer<typeof UserSchema>;
export type AuthResponse = z.infer<typeof AuthResponseSchema>;
export type MessageResponse = z.infer<typeof MessageResponseSchema>;
export type Farm = z.infer<typeof FarmSchema>;
export type WaterStress = z.infer<typeof WaterStressSchema>;
export type WaterSavingsRow = z.infer<typeof WaterSavingsRowSchema>;
export type StressSeverity = z.infer<typeof StressSeveritySchema>;
export type IrrigationEvent = z.infer<typeof IrrigationEventSchema>;

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function formatDetail(detail: unknown, status: number): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((err) => err?.msg ?? "Invalid input").join(", ");
  }
  return `Request failed with status ${status}`;
}

async function request<T>(
  schema: z.ZodSchema<T>,
  path: string,
  options: {
    method?: string;
    body?: unknown;
    signal?: AbortSignal;
  } = {},
): Promise<T> {
  const { method = "GET", body, signal } = options;
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    credentials: "include",
    headers: body
      ? {
          "Content-Type": "application/json",
        }
      : undefined,
    body: body ? JSON.stringify(body) : undefined,
    signal: signal ?? AbortSignal.timeout(10000),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const detail =
      data && typeof data === "object" && "detail" in data
        ? data.detail
        : undefined;
    throw new ApiError(formatDetail(detail, res.status), res.status);
  }

  return schema.parse(await res.json());
}

export async function signup(body: SignupRequest): Promise<AuthResponse> {
  return request(AuthResponseSchema, "/auth/signup", {
    method: "POST",
    body,
  });
}

export async function login(body: LoginRequest): Promise<AuthResponse> {
  return request(AuthResponseSchema, "/auth/login", {
    method: "POST",
    body,
  });
}

export async function forgotPassword(
  body: ForgotPasswordRequest,
): Promise<MessageResponse> {
  return request(MessageResponseSchema, "/auth/forgot-password", {
    method: "POST",
    body,
  });
}

export async function resetPassword(body: {
  token: string;
  new_password: string;
}): Promise<MessageResponse> {
  return request(MessageResponseSchema, "/auth/reset-password", {
    method: "POST",
    body,
  });
}

export async function logout(): Promise<MessageResponse> {
  return request(MessageResponseSchema, "/auth/logout", {
    method: "POST",
  });
}

export async function getMe(): Promise<User> {
  return request(UserSchema, "/auth/me");
}

export async function updateMe(body: {
  locale?: "en" | "es";
  is_socially_disadvantaged?: boolean | null;
  is_beginning_farmer?: boolean | null;
}): Promise<User> {
  return request(UserSchema, "/auth/me", { method: "PATCH", body });
}

// limit=100 is the backend's pagination cap; without it the API defaults to
// 10 and farms past the first page silently vanish from the UI.
export async function getFarms(): Promise<Farm[]> {
  return request(FarmsListSchema, "/farms/?limit=100");
}

export async function createFarm(
  body: Partial<Omit<Farm, "id" | "user_id" | "created_at">> & { name: string },
): Promise<Farm> {
  return request(FarmSchema, "/farms/", { method: "POST", body });
}

export async function getFarm(farmId: number): Promise<Farm> {
  return request(FarmSchema, `/farms/${farmId}`);
}

export async function updateFarm(
  farmId: number,
  body: Partial<Omit<Farm, "id" | "user_id" | "created_at">>,
): Promise<Farm> {
  return request(FarmSchema, `/farms/${farmId}`, { method: "PUT", body });
}

export async function deleteFarm(farmId: number): Promise<Farm> {
  return request(FarmSchema, `/farms/${farmId}`, { method: "DELETE" });
}

/** 404 means "no data yet" here — surfaced as null so the page can show an empty state. */
export async function getWaterStress(
  farmId: number,
): Promise<WaterStress | null> {
  try {
    return await request(WaterStressSchema, `/farms/${farmId}/water-stress`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

export async function getWaterSavings(
  farmId: number,
): Promise<WaterSavingsRow[]> {
  const page = await request(
    PaginatedWaterSavingsSchema,
    `/farms/${farmId}/water-savings?limit=100`,
  );
  return page.results;
}

export async function getBaselineIrrigations(
  farmId: number,
): Promise<BaselineIrrigation[]> {
  const page = await request(
    PaginatedBaselineSchema,
    `/farms/${farmId}/baseline-irrigations`,
  );
  return page.results;
}

export async function createBaselineIrrigation(
  farmId: number,
  gallonsPerWeek: number,
): Promise<BaselineIrrigation> {
  return request(
    BaselineIrrigationSchema,
    `/farms/${farmId}/baseline-irrigations`,
    { method: "POST", body: { gallons_per_week_estimate: gallonsPerWeek } },
  );
}

export const SavingsTotalsSchema = z.object({
  baseline_gallons: z.coerce.number(),
  actual_gallons: z.coerce.number(),
  gallons_saved: z.coerce.number(),
  kwh_saved: z.coerce.number(),
  co2_kg_saved: z.coerce.number(),
});

export const SavingsSeriesSchema = z.object({
  farm_id: z.number(),
  start_date: z.string(),
  end_date: z.string(),
  totals: SavingsTotalsSchema,
  results: z.array(WaterSavingsRowSchema),
});

export type SavingsSeries = z.infer<typeof SavingsSeriesSchema>;

export const ImpactStatsSchema = z.object({
  snapshot_date: z.string(),
  total_farms: z.number(),
  farms_green: z.number(),
  farms_yellow: z.number(),
  farms_red: z.number(),
  total_gallons_saved: z.coerce.number(),
  total_kwh_saved: z.coerce.number(),
  total_co2_kg_saved: z.coerce.number(),
  computed_at: z.string(),
});

export type ImpactStats = z.infer<typeof ImpactStatsSchema>;

export async function getSavingsSeries(
  farmId: number,
  from: string,
  to: string,
): Promise<SavingsSeries> {
  return request(
    SavingsSeriesSchema,
    `/farms/${farmId}/savings?from=${from}&to=${to}`,
  );
}

/** 404 = cohort too small or no snapshot yet — render the "coming soon" state. */
export async function getImpactStats(): Promise<ImpactStats | null> {
  try {
    return await request(ImpactStatsSchema, "/impact/stats");
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

/** Fetches the report with credentials and hands back a blob URL for download. */
export async function fetchSgmaReportBlobUrl(
  farmId: number,
  year: number,
  format: "csv" | "pdf",
): Promise<string> {
  const res = await fetch(
    `${API_BASE}/farms/${farmId}/sgma-export?year=${year}&format=${format}`,
    { credentials: "include" },
  );
  if (!res.ok) {
    throw new ApiError(`Export failed with status ${res.status}`, res.status);
  }
  return URL.createObjectURL(await res.blob());
}

export async function logIrrigationEvent(
  farmId: number,
  body: { event_date: string; gallons_applied: number },
): Promise<IrrigationEvent> {
  return request(IrrigationEventSchema, `/farms/${farmId}/irrigation-events`, {
    method: "POST",
    body,
  });
}
