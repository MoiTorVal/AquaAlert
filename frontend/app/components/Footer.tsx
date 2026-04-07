import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-zinc-950 border-t border-zinc-800">
      <div className="max-w-7xl mx-auto px-8 py-16">
        <div className="flex flex-col md:flex-row justify-between gap-12">
          {/* Brand */}
          <div className="max-w-sm">
            <Link href="/" className="text-white text-xl font-bold">
              WaterStress
            </Link>
            <p className="text-white/50 text-sm mt-4 leading-relaxed">
              Soil moisture monitoring and water stress predictions for
              agronomists and farmers.
            </p>
          </div>

          {/* Links */}
          <div className="flex gap-16">
            <div>
              <h4 className="text-white font-semibold text-sm mb-4">Product</h4>
              <ul className="flex flex-col gap-3">
                <li>
                  <Link
                    href="/login"
                    className="text-white/50 hover:text-amber-400 text-sm transition-colors"
                  >
                    Login
                  </Link>
                </li>
                <li>
                  <Link
                    href="/dashboard"
                    className="text-white/50 hover:text-amber-400 text-sm transition-colors"
                  >
                    Dashboard
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold text-sm mb-4">Company</h4>
              <ul className="flex flex-col gap-3">
                <li>
                  <Link
                    href="/contact"
                    className="text-white/50 hover:text-amber-400 text-sm transition-colors"
                  >
                    Contact
                  </Link>
                </li>
                <li>
                  <Link
                    href="/privacy"
                    className="text-white/50 hover:text-amber-400 text-sm transition-colors"
                  >
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link
                    href="/terms"
                    className="text-white/50 hover:text-amber-400 text-sm transition-colors"
                  >
                    Terms of Service
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-zinc-800 mt-12 pt-8 text-white/40 text-sm">
          &copy; {new Date().getFullYear()} WaterStress. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
