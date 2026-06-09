import "@testing-library/jest-dom/vitest";

// api.ts reads this at import time and throws when unset
process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";

// Node 22+ exposes a restricted global localStorage that shadows jsdom's and
// lacks working methods unless node runs with --localstorage-file. Replace it
// with a functional in-memory implementation for tests.
const store = new Map<string, string>();
Object.defineProperty(window, "localStorage", {
  configurable: true,
  value: {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, String(v)),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
    key: (i: number) => [...store.keys()][i] ?? null,
    get length() {
      return store.size;
    },
  },
});
