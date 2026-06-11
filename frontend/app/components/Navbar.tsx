"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import Logo from "./Logo";
import LocaleToggle from "./LocaleToggle";
import { useAuth } from "../context/AuthContext";
import { logout } from "../lib/api";

const navLink =
  "text-white/80 hover:text-white hover:bg-muted/20 px-3 py-1.5 rounded-lg transition-colors";

const mobileNavLink =
  "text-white/80 hover:text-white hover:bg-muted/20 px-3 py-2.5 rounded-lg transition-colors text-base";

export default function Navbar() {
  const t = useTranslations("navbar");
  const { user, setUser } = useAuth();

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
          <div className="hidden md:flex items-center gap-6 text-sm font-medium">
            <Link href="/" className={navLink}>
              {t("home")}
            </Link>
            {user && (
              <Link href="/farms" className={navLink}>
                {t("myFarms")}
              </Link>
            )}
            <Link href="/contact" className={navLink}>
              {t("contact")}
            </Link>
            <LocaleToggle />
            <span className="w-px h-4 bg-white/20" />
            {user ? (
              <button
                className={navLink}
                onClick={() =>
                  logout()
                    .then(() => setUser(null))
                    .catch(() => setUser(null))
                }
              >
                {t("logout")}
              </button>
            ) : (
              <>
                <Link href="/login" className={navLink}>
                  {t("login")}
                </Link>
                <Link
                  href="/signup"
                  className="bg-btn-secondary hover:bg-white text-btn-text font-semibold px-4 py-1.5
  rounded-lg transition-colors"
                >
                  {t("signup")}
                </Link>
              </>
            )}
          </div>
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
          <div className="px-3 py-1">
            <LocaleToggle />
          </div>
          <Link
            href="/"
            className={mobileNavLink}
            onClick={() => setMenuOpen(false)}
          >
            {t("home")}
          </Link>
          {user && (
            <Link
              href="/farms"
              className={mobileNavLink}
              onClick={() => setMenuOpen(false)}
            >
              {t("myFarms")}
            </Link>
          )}
          <Link
            href="/contact"
            className={mobileNavLink}
            onClick={() => setMenuOpen(false)}
          >
            {t("contact")}
          </Link>
          {user ? (
            <button
              className={mobileNavLink}
              onClick={() => {
                logout()
                  .then(() => setUser(null))
                  .catch(() => setUser(null));
                setMenuOpen(false);
              }}
            >
              {t("logout")}
            </button>
          ) : (
            <>
              <Link
                href="/login"
                className={mobileNavLink}
                onClick={() => setMenuOpen(false)}
              >
                {t("login")}
              </Link>
              <Link
                href="/signup"
                className="bg-btn-secondary hover:bg-white text-btn-text font-semibold px-4 py-2.5 rounded-lg
transition-colors text-center mt-2"
                onClick={() => setMenuOpen(false)}
              >
                {t("signup")}
              </Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
