"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import Logo from "./Logo";

const navLink =
  "text-white/60 hover:text-white hover:bg-[#8A8F98]/20 px-3 py-1.5 rounded-lg transition-colors";

const mobileNavLink =
  "text-white/60 hover:text-white hover:bg-[#8A8F98]/20 px-3 py-2.5 rounded-lg transition-colors text-base";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

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
      className={`fixed top-0 left-0 right-0 w-full z-50 transition-colors duration-300 border-b border-white/10  
  ${scrolled || menuOpen ? "bg-zinc-950 border-zinc-800" : "bg-zinc-950/80 backdrop-blur-md"}`}
    >
      <div className="max-w-7xl mx-auto px-8 py-6 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-1">
          <Logo />
          <span className="text-white text-lg font-semibold tracking-tight">
            WaterStress
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-6 text-sm font-medium">
          <Link href="/" className={navLink}>
            Home
          </Link>
          <Link href="/contact" className={navLink}>
            Contact
          </Link>
          <span className="w-px h-4 bg-white/20" />
          <Link href="/login" className={navLink}>
            Log In
          </Link>
          <Link
            href="/signup"
            className="bg-[#E6E6E6] hover:bg-white text-[#08090A] font-semibold px-4 py-1.5 rounded-lg
  transition-colors"
          >
            Sign up
          </Link>
        </div>

        {/* Hamburger button */}
        <button
          className="md:hidden text-white p-2"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            {menuOpen ? (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            ) : (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4 6h16M4 12h16M4 18h16"
              />
            )}
          </svg>
        </button>
      </div>
      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-white/10 px-8 py-4 flex flex-col gap-2 text-sm font-medium">
          <Link
            href="/"
            className={mobileNavLink}
            onClick={() => setMenuOpen(false)}
          >
            Home
          </Link>
          <Link
            href="/contact"
            className={mobileNavLink}
            onClick={() => setMenuOpen(false)}
          >
            Contact
          </Link>
          <Link
            href="/login"
            className={mobileNavLink}
            onClick={() => setMenuOpen(false)}
          >
            Log In
          </Link>
          <Link
            href="/signup"
            className="bg-[#E6E6E6] hover:bg-white text-[#08090A] font-semibold px-4 py-2.5 rounded-lg
  transition-colors text-center mt-2"
            onClick={() => setMenuOpen(false)}
          >
            Sign up
          </Link>
        </div>
      )}
    </nav>
  );
}
