import Link from "next/link";
import ForgotPasswordForm from "./ForgotPasswordForm";
export const metadata = {
  title: "Forgot Password | WaterStress",
  description: "Reset your WaterStress password",
};

export default function ForgotPasswordPage() {
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
            <p className="text-muted text-sm mt-1">Reset your password</p>
          </div>

          <ForgotPasswordForm />
        </div>

        <p className="text-center text-sm text-muted mt-6">
          Remember your password?{" "}
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
