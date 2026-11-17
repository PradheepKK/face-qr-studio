"use client";

import { useSyncExternalStore } from "react";
import { Moon, Sun } from "lucide-react";

// Theme maarina subscribers-ku therivikka
const listeners = new Set<() => void>();

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

// Browser-la ippo dark irukka nu <html> class-la irundhu padikkum
function getSnapshot() {
  return document.documentElement.classList.contains("dark");
}

// Server-la theme theriyaadhu, so light nu vachukkalam
function getServerSnapshot() {
  return false;
}

// Theme apply panna + save panna
function applyTheme(isDark: boolean) {
  document.documentElement.classList.toggle("dark", isDark);
  localStorage.setItem("theme", isDark ? "dark" : "light");
  listeners.forEach((l) => l());
}

export default function ThemeToggle() {
  const dark = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const toggle = () => applyTheme(!dark);

  return (
    <button
      onClick={toggle}
      aria-label="Theme maathu"
      className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
    >
      {dark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  );
}