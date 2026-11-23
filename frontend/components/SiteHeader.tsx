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
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 font-bold">
          <ScanFace className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
          <span className="hidden sm:inline">Face QR Studio</span>
        </Link>

        <nav className="flex items-center gap-1">
          {TABS.map(({ href, label, icon: Icon }) => {
            const active = path === href;
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  active
                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300"
                    : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </nav>

        <ThemeToggle />
      </div>
    </header>
  );
}