"use client";

import { useState } from "react";
import { Moon, Sun, ScanFace, QrCode } from "lucide-react";

export default function Home() {
  // Dark mode on/off state
  const [dark, setDark] = useState(false);

  // Button click panna html tag-la "dark" class add/remove aagum
  const toggleTheme = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-lg dark:border-slate-700 dark:bg-slate-900">
        <div className="mb-6 flex items-center gap-3">
          <ScanFace className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
          <QrCode className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
        </div>

        <h1 className="text-2xl font-bold">Face QR Studio</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Step 2 setup test: Next.js + TypeScript + Tailwind + Lucide work
          aagudhu.
        </p>

        <button
          onClick={toggleTheme}
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700"
        >
          {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          {dark ? "Light mode" : "Dark mode"}
        </button>
      </div>
    </main>
  );
}