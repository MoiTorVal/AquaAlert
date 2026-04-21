"use client";

import { useState } from "react";
import Link from "next/link";
import Input from "../components/Input";
import Spinner from "../components/Spinner";
import { signup } from "../lib/api";
import { useRouter } from "next/navigation";

interface FormFields {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

function validate(fields: FormFields): FormErrors {
  const errors: FormErrors = {};
  if (!fields.name.trim()) errors.name = "Name is required";
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
  if (!fields.confirmPassword.trim()) {
    errors.confirmPassword = "Please confirm your password";
  } else if (fields.password !== fields.confirmPassword) {
    errors.confirmPassword = "Passwords do not match";
  }
  return errors;
}

export default function SignupPage() {
  const router = useRouter();
  const [fields, setFields] = useState<FormFields>({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

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
    setServerError(null);
    try {
      const { user } = await signup(fields);
      router.push("/dashboard");
    } catch (error) {
      setServerError(
        error instanceof Error ? error.message : "An error occurred",
      );
    } finally {
      setLoading(false);
    }
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
            <p className="text-muted text-sm mt-1">Create your account</p>
          </div>

          <form
            onSubmit={handleSubmit}
            noValidate
            className="flex flex-col gap-5"
          >
            <Input
              label="Name"
              name="name"
              value={fields.name}
              onChange={handleChange}
              placeholder="John Smith"
              error={errors.name}
            />

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

            <Input
              label="Confirm Password"
              name="confirmPassword"
              type="password"
              value={fields.confirmPassword}
              onChange={handleChange}
              placeholder="••••••••"
              error={errors.confirmPassword}
            />

            <button
              type="submit"
              disabled={loading}
              className="bg-btn-secondary hover:bg-white disabled:opacity-50 text-btn-text font-semibold py-3
  rounded-lg transition-colors mt-2"
            >
              {loading ? <Spinner /> : "Create Account"}
            </button>
            {serverError && (
              <p className="text-red-500 text-sm mt-2">{serverError}</p>
            )}
          </form>
        </div>

        <p className="text-center text-sm text-muted mt-6">
          Already have an account?{" "}
          <Link
            href="/login"
            className="text-surface hover:text-white hover:underline font-medium"
          >
            Log In
          </Link>
        </p>
      </div>
    </main>
  );
}
