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

export const UserSchema = z.object({
  id: z.number(),
  email: z.string(),
  name: z.string().nullable(),
});

export const AuthResponseSchema = z.object({
  message: z.string(),
  user: UserSchema,
});

export const MessageResponseSchema = z.object({
  message: z.string(),
});

export type User = z.infer<typeof UserSchema>;
export type AuthResponse = z.infer<typeof AuthResponseSchema>;
export type MessageResponse = z.infer<typeof MessageResponseSchema>;

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
