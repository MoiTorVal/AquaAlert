import Link from "next/link";
import Logo from "./Logo";

export default function Footer() {
  return (
    <footer className="bg-[#0a0a0a] border-t border-white/10">
      <div className="max-w-7xl mx-auto px-8 py-16">
        <div className="flex flex-col md:flex-row justify-between gap-12">
          {/* Brand */}
          <div className="max-w-sm">
            <Link href="/" className="flex items-center gap-1">
              <Logo />
              <span className="text-[#F7F8F8] text-lg font-semibold">
                WaterStress
              </span>
            </Link>
            <p className="text-[#8A8F98] text-sm mt-4 leading-relaxed">
              Soil moisture monitoring and water stress predictions for farmers.
            </p>
          </div>

          {/* Links */}
          <div className="flex gap-16">
            <div>
              <h4 className="text-[#F7F8F8] font-semibold text-sm mb-4">
                Product
              </h4>
              <ul className="flex flex-col gap-3">
                <li>
                  <Link
                    href="/login"
                    className="text-[#8A8F98] hover:text-white text-sm transition-colors"
                  >
                    Login
                  </Link>
                </li>
                <li>
                  <Link
                    href="/demo"
                    className="text-[#8A8F98] hover:text-white text-sm transition-colors"
                  >
                    Demo
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-[#F7F8F8] font-semibold text-sm mb-4">
                Company
              </h4>
              <ul className="flex flex-col gap-3">
                <li>
                  <Link
                    href="/contact"
                    className="text-[#8A8F98] hover:text-white text-sm transition-colors"
                  >
                    Contact
                  </Link>
                </li>
                <li>
                  <Link
                    href="/privacy"
                    className="text-[#8A8F98] hover:text-white text-sm transition-colors"
                  >
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link
                    href="/terms"
                    className="text-[#8A8F98] hover:text-white text-sm transition-colors"
                  >
                    Terms of Service
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Bottom bar */}

        <div className="border-t border-white/10 mt-12 pt-8 text-[#8A8F98] text-sm">
          &copy; {new Date().getFullYear()} WaterStress. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
