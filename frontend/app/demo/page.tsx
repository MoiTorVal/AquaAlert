import Link from "next/link";

export const metadata = {
  title: "Demo | WaterStress",
  description: "Try the WaterStress demo",
};

export default function DemoPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0a] flex items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-[#F7F8F8] mb-4">
          Demo coming soon
        </h1>
        <p className="text-[#8A8F98] mb-8">
          We&apos;re building something worth waiting for.
        </p>
        <Link
          href="/"
          className="text-[#E6E6E6] hover:text-white hover:underline text-sm font-medium"
        >
          Back to home
        </Link>
      </div>
    </main>
  );
}
