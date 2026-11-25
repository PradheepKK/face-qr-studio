import Link from "next/link";
import { ScanFace, ShieldCheck } from "lucide-react";

export default function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white/60 dark:border-slate-800 dark:bg-slate-950/60">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 text-sm text-slate-500 sm:flex-row sm:px-6">
        <div className="flex items-center gap-2 font-semibold text-slate-700 dark:text-slate-200">
          <ScanFace className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
          Face QR Studio
        </div>

        <nav className="flex items-center gap-5">
          <Link href="/" className="hover:text-indigo-600 dark:hover:text-indigo-400">
            Face QR
          </Link>
          <Link href="/url-qr" className="hover:text-indigo-600 dark:hover:text-indigo-400">
            URL → QR
          </Link>
        </nav>

        <p className="flex items-center gap-1.5 text-center">
          <ShieldCheck className="h-4 w-4 text-emerald-500" />
          Photos store aagaadhu. Memory-la mattum process.
        </p>
      </div>
    </footer>
  );
}