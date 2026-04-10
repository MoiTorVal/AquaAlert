"use client";

import { useState } from "react";
import Input from "../components/Input";
import Spinner from "../components/Spinner";

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
        <h2 className="text-xl font-semibold text-surface mb-2">
          Check your inbox
        </h2>
        <p className="text-muted text-sm">
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
        className="bg-btn-secondary hover:bg-white disabled:opacity-50 text-btn-text font-semibold py-3 rounded-lg 
  transition-colors mt-2"
      >
        {loading ? <Spinner /> : "Send Reset Link"}
      </button>
    </form>
  );
}
