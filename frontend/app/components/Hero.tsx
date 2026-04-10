"use client";
import Link from "next/link";
import { motion } from "framer-motion";

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center pt-24">
      <div className="absolute inset-0 bg-bg-primary" />

      <div className="relative z-10 max-w-7xl mx-auto px-8 w-full grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        {/* Left — text */}
        <div>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.1, ease: "easeOut", delay: 0.3 }}
            className="text-surface text-3xl sm:text-5xl md:text-7xl font-bold leading-tight"
          >
            Know when your crops need water before they stress
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.0, ease: "easeOut", delay: 0.6 }}
            className="text-white/70 text-lg mt-6 max-w-xl"
          >
            Get real-time soil moisture and weather data delivered to your
            device so you can make smarter irrigation decisions.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.1, ease: "easeOut", delay: 0.6 }}
            className="flex gap-4 mt-10"
          >
            <Link
              href="/login"
              className="bg-btn-secondary hover:bg-white text-btn-text font-semibold px-6 py-2 rounded-lg transition-colors text-sm"
            >
              Get Started
            </Link>

            {/* Secondary — ghost */}
            <Link
              href="/contact"
              className="border border-white/20 hover:border-white/40 text-white/70 hover:text-white font-semibold px-6 py-2 rounded-lg transition-colors text-sm"
            >
              Learn More
            </Link>
          </motion.div>
        </div>

        {/* Right — demo preview */}
        <motion.div
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1.2, ease: "easeOut", delay: 0.5 }}
        >
          <div className="bg-white/5 border border-white/10 rounded-2xl aspect-[4/3] flex flex-col items-center justify-center gap-4">
            <p className="text-muted text-sm">See it in action</p>
            <Link
              href="/demo"
              className="bg-btn-secondary hover:bg-white text-btn-text font-semibold px-6 py-2.5 rounded-lg transition-colors text-sm"
            >
              Try the Demo
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
