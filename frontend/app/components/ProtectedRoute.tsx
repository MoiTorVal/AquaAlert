"use client";
import Link from "next/link";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!user) {
    return <SignInGate />;
  }

  return <>{children}</>;
}

function SignInGate() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 pt-28 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
        <svg
          className="h-8 w-8 text-gray-500"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.8}
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M16.5 10.5V7a4.5 4.5 0 10-9 0v3.5m-.75 11h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
          />
        </svg>
      </div>
      <h1 className="mt-5 text-xl font-semibold">Sign in to see your farms</h1>
      <p className="mt-2 max-w-sm text-sm text-gray-500">
        This page is only available to signed-in users. Log in to view your
        farms, water-stress alerts, and savings.
      </p>
      <div className="mt-6 flex flex-col items-center gap-3">
        <Link
          href="/login"
          className="rounded-lg bg-green-600 px-8 py-2.5 text-sm font-medium text-white hover:bg-green-700"
        >
          Log In
        </Link>
        <Link
          href="/signup"
          className="text-sm font-medium text-green-700 hover:underline"
        >
          Create an account
        </Link>
        <Link href="/" className="text-sm text-gray-500 hover:underline">
          Go back home
        </Link>
      </div>
    </main>
  );
}
