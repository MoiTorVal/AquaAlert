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
  area_hectares: z.number().nullable(),
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

export type User = z.infer<typeof UserSchema>;
export type AuthResponse = z.infer<typeof AuthResponseSchema>;
export type MessageResponse = z.infer<typeof MessageResponseSchema>;
export type Farm = z.infer<typeof FarmSchema>;

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
    throw new Error(formatDetail(detail, res.status));
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

export async function getFarms(): Promise<Farm[]> {
  return request(FarmsListSchema, "/farms");
}
