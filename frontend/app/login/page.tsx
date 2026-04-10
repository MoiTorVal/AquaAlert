"use client";

import { useState } from "react";
import Link from "next/link";
import Input from "../components/Input";
import Spinner from "../components/Spinner";

interface FormFields {
  email: string;
  password: string;
}

interface FormErrors {
  email?: string;
  password?: string;
}

function validate(fields: FormFields): FormErrors {
  const errors: FormErrors = {};
  if (!fields.email.trim()) {
    errors.email = "Email is required";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fields.email)) {
    errors.email = "Invalid email format";
  }
  if (!fields.password.trim()) {
    errors.password = "Password is required";
  } else if (fields.password.length < 6) {
    errors.password = "Password must be at least 6 characters";
  }
  return errors;
}

export default function LoginPage() {
  const [fields, setFields] = useState<FormFields>({
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) {
    const { name, value } = e.target;
    setFields((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const validationErrors = validate(fields);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-bg-primary flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white/5 rounded-2xl border border-white/10 px-10 py-10">
          <div className="text-center mb-8">
            <Link
              href="/"
              className="text-2xl font-bold text-surface tracking-tight"
            >
              WaterStress
            </Link>
            <p className="text-text-muted text-sm mt-1">
              Sign in to your account
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            noValidate
            className="flex flex-col gap-5"
          >
            <Input
              label="Email"
              name="email"
              type="email"
              value={fields.email}
              onChange={handleChange}
              placeholder="you@example.com"
              error={errors.email}
            />

            <Input
              label="Password"
              name="password"
              type="password"
              value={fields.password}
              onChange={handleChange}
              placeholder="••••••••"
              error={errors.password}
            />

            <button
              type="submit"
              disabled={loading}
              className="bg-[#E6E6E6] hover:bg-white disabled:opacity-50 text-[#08090A] font-semibold py-3
rounded-lg transition-colors mt-2"
            >
              {loading ? <Spinner /> : "Log In"}
            </button>
          </form>

          <div className="text-center mt-6">
            <Link
              href="/forgot-password"
              className="text-text-muted hover:text-white hover:underline text-sm"
            >
              Forgot password?
            </Link>
          </div>
        </div>

        <p className="text-center text-sm text-text-muted mt-6">
          Don&apos;t have an account?{" "}
          <Link
            href="/signup"
            className="text-surface hover:text-white hover:underline font-medium"
          >
            Create Account
          </Link>
        </p>
      </div>
    </main>
  );
}
