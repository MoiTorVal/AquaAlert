"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Input from "../components/Input";
import Spinner from "../components/Spinner";
import { forgotPassword } from "../lib/api";
import {
  ForgotPasswordFormSchema,
  type ForgotPasswordFormValues,
} from "../lib/validators";

export default function ForgotPasswordForm() {
  const [serverError, setServerError] = useState<string | null>(null);
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(ForgotPasswordFormSchema),
  });

  async function onValid(values: ForgotPasswordFormValues) {
    setServerError(null);
    try {
      await forgotPassword(values);
      setSubmittedEmail(values.email);
    } catch (error) {
      setServerError(
        error instanceof Error ? error.message : "An error occurred",
      );
    }
  }

  if (submittedEmail) {
    return (
      <div className="text-center py-4">
        <h2 className="text-xl font-semibold text-surface mb-2">
          Check your inbox
        </h2>
        <p className="text-muted text-sm">
          If an account exists for {submittedEmail}, we&apos;ll send a reset
          link.
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit(onValid)}
      noValidate
      className="flex flex-col gap-5"
    >
      <Input
        label="Email"
        type="email"
        placeholder="you@example.com"
        error={errors.email?.message}
        {...register("email")}
      />

      <button
        type="submit"
        disabled={isSubmitting}
        className="bg-btn-secondary hover:bg-white disabled:opacity-50 text-btn-text font-semibold py-3 rounded-lg transition-colors mt-2"
      >
        {isSubmitting ? <Spinner /> : "Send Reset Link"}
      </button>
      {serverError && (
        <p className="text-red-500 text-sm mt-2">{serverError}</p>
      )}
    </form>
  );
}
