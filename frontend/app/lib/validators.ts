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
export type LoginFormValues = z.infer<typeof LoginFormSchema>;
export type SignupFormValues = z.infer<typeof SignupFormSchema>;
export type ForgotPasswordFormValues = z.infer<typeof ForgotPasswordFormSchema>;
export type ResetPasswordFormValues = z.infer<typeof ResetPasswordFormSchema>;
