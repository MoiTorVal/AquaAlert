"use client";

import { useState } from "react";
import Input from "../components/Input";

export default function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email.trim()) {
      setError("Email is required");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("Invalid email format");
      return;
    }
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setLoading(false);
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <div className="text-center py-4">
        <h2 className="text-xl font-semibold text-[#F7F8F8] mb-2">
          Check your inbox
        </h2>
        <p className="text-[#8A8F98] text-sm">
          If an account exists for {email}, we&apos;ll send a reset link.
        </p>
      </div>
    );
  }
  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">
      <Input
        label="Email"
        name="email"
        type="email"
        value={email}
        onChange={(e) => {
          setEmail(e.target.value);
          setError("");
        }}
        placeholder="you@example.com"
        error={error}
      />

      <button
        type="submit"
        disabled={loading}
        className="bg-[#E6E6E6] hover:bg-white disabled:opacity-50 text-[#08090A] font-semibold py-3 rounded-lg 
  transition-colors mt-2"
      >
        {loading ? (
          <svg
            className="animate-spin h-5 w-5 mx-auto text-[#08090A]"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            />
          </svg>
        ) : (
          "Send Reset Link"
        )}
      </button>
    </form>
  );
}
