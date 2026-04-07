"use client";

import Link from "next/link";
import { useState, useEffect } from "react";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 60);
    };

    window.addEventListener("scroll", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 w-full z-50 transition-colors duration-300 ${
        scrolled ? "bg-zinc-950 border-b border-zinc-800" : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-8 py-6 flex items-center justify-between">
        <Link href="/" className="text-white text-xl font-bold tracking-tight">
          WaterStress
        </Link>
        <div className="flex gap-8 text-sm font-medium">
          <Link
            href="/"
            className="text-white/80 hover:text-amber-400 transition-colors"
          >
            HOME
          </Link>
          <Link
            href="/contact"
            className="text-white/80 hover:text-amber-400 transition-colors"
          >
            CONTACT
          </Link>
          <Link
            href="/login"
            className="text-white/80 hover:text-amber-400 transition-colors"
          >
            LOGIN
          </Link>
        </div>
      </div>
    </nav>
  );
}
