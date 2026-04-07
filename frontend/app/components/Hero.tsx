import Link from "next/link";

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center">
      {/* Background overlay */}
      <div className="absolute inset-0 bg-zinc-900" />

      {/* Content */}
      <div className="relative z-1 max-w-7xl mx-auto px-8 w-full">
        <p className="text-amber-400 text-sm font-semibold tracking-widest uppercase mb-4">
          Water Stress Monitoring
        </p>

        <h1 className="text-5xl md:text-7xl font-bold text-white leading-tight max-w-3xl">
          Know when your crops need water before they stress
        </h1>

        <p className="text-white/70 text-lg mt-6 max-w-xl">
          Get real-time soil moisture and weather data delivered to your device
          so you can make smarter irrigation decisions.
        </p>

        <div className="flex gap-4 mt-10">
          <Link
            href="/login"
            className="bg-amber-500 hover:bg-amber-400 text-zinc-900 font-semibold px-8 py-3 rounded-full        
  transition-colors"
          >
            Get Started
          </Link>
          <Link
            href="/contact"
            className="border border-white/30 hover:border-white text-white font-semibold px-8 py-3 rounded-full 
  transition-colors"
          >
            Learn More
          </Link>
        </div>
      </div>
    </section>
  );
}
