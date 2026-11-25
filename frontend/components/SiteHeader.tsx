"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ScanFace, Link2 } from "lucide-react";
import ThemeToggle from "./ThemeToggle";

const TABS = [
  { href: "/", label: "Face QR", icon: ScanFace },
  { href: "/url-qr", label: "URL → QR", icon: Link2 },
];

export default function SiteHeader() {
  const path = usePathname();

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/75 backdrop-blur-lg dark:border-slate-800/70 dark:bg-slate-950/75">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-2 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5 font-bold tracking-tight">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-violet-500 text-white shadow-sm">
            <ScanFace className="h-5 w-5" />
          </span>
          <span className="hidden text-base sm:inline">Face QR Studio</span>
        </Link>

        {/* Segmented tabs */}
        <nav
          aria-label="Main"
          className="flex items-center rounded-xl bg-slate-100 p-1 dark:bg-slate-800/70"
        >
          {TABS.map(({ href, label, icon: Icon }) => {
            const active = path === href;
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`inline-flex min-h-9 items-center gap-1.5 rounded-lg px-3 text-sm font-medium transition sm:px-4 ${
                  active
                    ? "bg-white text-indigo-700 shadow-sm dark:bg-slate-900 dark:text-indigo-300"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        <ThemeToggle />
      </div>
    </header>
  );
}