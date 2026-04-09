import Link from "next/link";
import ForgotPasswordForm from "./ForgotpasswordForm";

export const metadata = {
  title: "Forgot Password | WaterStress",
  description: "Reset your WaterStress password",
};

export default function ForgotPasswordPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0a] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white/5 rounded-2xl border border-white/10 px-10 py-10">
          <div className="text-center mb-8">
            <Link
              href="/"
              className="text-2xl font-bold text-[#F7F8F8] tracking-tight"
            >
              WaterStress
            </Link>
            <p className="text-[#8A8F98] text-sm mt-1">Reset your password</p>
          </div>

          <ForgotPasswordForm />
        </div>

        <p className="text-center text-sm text-[#8A8F98] mt-6">
          Remember your password?{" "}
          <Link
            href="/login"
            className="text-[#E6E6E6] hover:text-white hover:underline font-medium"
          >
            Log In
          </Link>
        </p>
      </div>
    </main>
  );
}
