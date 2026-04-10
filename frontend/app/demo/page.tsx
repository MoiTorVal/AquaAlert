import Link from "next/link";

export const metadata = {
  title: "Demo | WaterStress",
  description: "Try the WaterStress demo",
};

export default function DemoPage() {
  return (
    <main className="min-h-screen bg-bg-primary flex items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-surface mb-4">
          Demo coming soon
        </h1>
        <p className="text-muted mb-8">
          We&apos;re building something worth waiting for.
        </p>
        <Link
          href="/"
          className="text-surface hover:text-white hover:underline text-sm font-medium"
        >
          Back to home
        </Link>
      </div>
    </main>
  );
}
