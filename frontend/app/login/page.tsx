"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Input from "../components/Input";
import Spinner from "../components/Spinner";
import { login } from "../lib/api";
import { LoginFormSchema, type LoginFormValues } from "../lib/validators";

export default function LoginPage() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(LoginFormSchema),
  });

  async function onValid(values: LoginFormValues) {
    setServerError(null);
    try {
      await login(values);
      router.push("/dashboard");
    } catch (error) {
      setServerError(
        error instanceof Error ? error.message : "An error occurred",
      );
    }
  }

  return (
    <main className="min-h-screen bg-bg-primary flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white/5 rounded-2xl border border-white/10 px-10 py-10">
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
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              error={errors.password?.message}
              {...register("password")}
            />
            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-[#E6E6E6] hover:bg-white disabled:opacity-50 text-[#08090A] font-semibold py-3 rounded-lg"
            >
              {isSubmitting ? <Spinner /> : "Log In"}
            </button>
            {serverError && (
              <p className="text-red-500 text-sm mt-2">{serverError}</p>
            )}
          </form>
        </div>
      </div>
    </main>
  );
}
