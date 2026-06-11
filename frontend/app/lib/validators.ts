import { z } from "zod";

const PASSWORD_MIN_LENGTH = 8;

const emailField = z
  .string()
  .trim()
  .min(1, "Email is required")
  .email("Invalid email format");

const passwordField = z
  .string()
  .min(1, "Password is required")
  .min(
    PASSWORD_MIN_LENGTH,
    `Password must be at least ${PASSWORD_MIN_LENGTH} characters`,
  );

export const LoginFormSchema = z.object({
  email: emailField,
  password: passwordField,
});

export const SignupFormSchema = z
  .object({
    email: emailField,
    password: passwordField,
    name: z.string().trim().min(1, "Name is required"),
    confirmPassword: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export const ResetPasswordFormSchema = z
  .object({
    new_password: passwordField,
    confirmPassword: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.new_password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export const ForgotPasswordFormSchema = z.object({ email: emailField });

// Number inputs stay strings in the form (clean react-hook-form types) and are
// converted in gallonsFromForm after validation.
const requiredPositive = (
  ctx: z.RefinementCtx,
  field: string,
  label: string,
  raw: string | undefined,
) => {
  if (!raw || raw.trim() === "") {
    ctx.addIssue({ code: "custom", path: [field], message: `${label} is required` });
    return;
  }
  const n = Number(raw);
  if (Number.isNaN(n) || n <= 0) {
    ctx.addIssue({ code: "custom", path: [field], message: "Must be more than 0" });
  }
};

export const IrrigationLogFormSchema = z
  .object({
    event_date: z
      .string()
      .min(1, "Date is required")
      .refine((d) => !Number.isNaN(Date.parse(d)), "Invalid date")
      .refine(
        (d) => Date.parse(d) <= Date.now(),
        "Date cannot be in the future",
      ),
    mode: z.enum(["gallons", "runtime"]),
    gallons: z.string().optional(),
    hours: z.string().optional(),
    gpm: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.mode === "gallons") {
      requiredPositive(ctx, "gallons", "Gallons", data.gallons);
    } else {
      requiredPositive(ctx, "hours", "Hours", data.hours);
      requiredPositive(ctx, "gpm", "Pump flow (GPM)", data.gpm);
    }
  });

/** Runtime mode: hours x GPM x 60 min/hr -> total gallons. */
export function gallonsFromForm(values: IrrigationLogFormValues): number {
  if (values.mode === "gallons") return Number(values.gallons);
  return Math.round(Number(values.hours) * Number(values.gpm) * 60);
}

export const SOIL_TEXTURES = [
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
] as const;

/** "SandyClayLoam" -> "Sandy Clay Loam" — display only; the API keeps the enum value. */
export function soilLabel(value: string): string {
  return value.replace(/([a-z])([A-Z])/g, "$1 $2");
}

export const CreateFarmFormSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  location: z.string().trim().optional(),
  crop_type: z.string().trim().optional(),
  planting_date: z.string().optional(),
  soil_type: z.enum(SOIL_TEXTURES).or(z.literal("")).optional(),
  acreage_acres: z
    .string()
    .optional()
    .refine(
      (v) => !v || (!Number.isNaN(Number(v)) && Number(v) > 0),
      "Must be more than 0",
    ),
});

export const EditFarmFormSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  location: z.string().trim().optional(),
  crop_type: z.string().trim().optional(),
  planting_date: z.string().optional(),
  soil_type: z.enum(SOIL_TEXTURES).or(z.literal("")).optional(),
  acreage_acres: z
    .string()
    .optional()
    .refine(
      (v) => !v || (!Number.isNaN(Number(v)) && Number(v) > 0),
      "Must be more than 0",
    ),
});

export type CreateFarmFormValues = z.infer<typeof CreateFarmFormSchema>;

export type IrrigationLogFormValues = z.infer<typeof IrrigationLogFormSchema>;
export type EditFarmFormValues = z.infer<typeof EditFarmFormSchema>;
export type LoginFormValues = z.infer<typeof LoginFormSchema>;
export type SignupFormValues = z.infer<typeof SignupFormSchema>;
export type ForgotPasswordFormValues = z.infer<typeof ForgotPasswordFormSchema>;
export type ResetPasswordFormValues = z.infer<typeof ResetPasswordFormSchema>;
