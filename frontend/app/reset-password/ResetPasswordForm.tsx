"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Input from "../components/Input";
import Spinner from "../components/Spinner";
import { resetPassword } from "../lib/api";
import {
  ResetPasswordFormSchema,
  ResetPasswordFormValues,
} from "../lib/validators";
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/navigation";

export default function ResetPasswordForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(ResetPasswordFormSchema),
    mode: "onBlur",
  });

  async function onValid(values: ResetPasswordFormValues) {
    setServerError(null);
    try {
      await resetPassword({
        token: token ?? "",
        new_password: values.new_password,
      });
      router.push("/login?reset=success");
    } catch (error) {
      setServerError(
        error instanceof Error ? error.message : "An error occurred",
      );
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onValid)}
      noValidate
      className="flex flex-col gap-5"
    >
      <Input
        label="New Password"
        type="password"
        placeholder="••••••••"
        autoComplete="new-password"
        error={errors.new_password?.message}
        {...register("new_password")}
      />
      <Input
        label="Confirm Password"
        type="password"
        placeholder="••••••••"
        autoComplete="new-password"
        error={errors.confirmPassword?.message}
        {...register("confirmPassword")}
      />
      <button
        type="submit"
        disabled={isSubmitting}
        className="bg-btn-secondary hover:bg-white disabled:opacity-50 text-btn-text font-semibold py-3 rounded-lg 
  transition-colors mt-2"
      >
        {isSubmitting ? <Spinner /> : "Reset Password"}
      </button>
      {serverError && (
        <p role="alert" className="text-red-500 text-sm mt-2">
          {serverError}
        </p>
      )}
    </form>
  );
}
