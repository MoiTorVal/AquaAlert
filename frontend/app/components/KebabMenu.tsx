"use client";

import { useEffect, useRef, useState } from "react";

export type KebabMenuItem = {
  label: string;
  onSelect: () => void;
  danger?: boolean;
};

/** Three-dot menu for row actions, so Edit/Delete don't shout from every
 * row. Clicks never bubble to the row (rows often navigate). */
export default function KebabMenu({
  ariaLabel,
  items,
}: {
  ariaLabel: string;
  items: KebabMenuItem[];
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  return (
    <div
      ref={ref}
      className="relative inline-block"
      onClick={(e) => e.stopPropagation()}
    >
      <button
        aria-label={ariaLabel}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
      >
        <span aria-hidden className="text-lg leading-none">⋯</span>
      </button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 z-10 mt-1 w-28 rounded-lg border border-gray-200 bg-white py-1 text-left shadow-lg"
        >
          {items.map((item) => (
            <button
              key={item.label}
              role="menuitem"
              onClick={() => {
                setOpen(false);
                item.onSelect();
              }}
              className={`block w-full px-3 py-1.5 text-left ${
                item.danger
                  ? "text-red-600 hover:bg-red-50"
                  : "text-gray-700 hover:bg-gray-50"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
