"use client";

import { useState } from "react";
import { ScanFace, QrCode, Sparkles, ShieldCheck, Check, Circle } from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";
import UploadCard from "@/components/UploadCard";
import StyleOptions from "@/components/StyleOptions";
import ResultPreview from "@/components/ResultPreview";
import DownloadPanel from "@/components/DownloadPanel";
import { PERSON_TYPES, QR_TYPES } from "@/lib/validate";
import {
  DEFAULT_SETTINGS,
  type Settings,
  type ValidationStatus,
} from "@/lib/types";

// Section heading (number + title). Component-a Home-ku veliya declare pannirukken.
function Step({ n, title }: { n: number; title: string }) {
  return (
    <h2 className="mb-4 flex items-center gap-3 text-xl font-semibold">
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-sm text-white">
        {n}
      </span>
      {title}
    </h2>
  );
}

// Checklist row (tick / empty circle)
function CheckItem({ ok, text }: { ok: boolean; text: string }) {
  return (
    <li className="flex items-center gap-2 text-sm">
      {ok ? (
        <Check className="h-4 w-4 text-emerald-500" />
      ) : (
        <Circle className="h-4 w-4 text-slate-400" />
      )}
      <span className={ok ? "" : "text-slate-500"}>{text}</span>
    </li>
  );
}

export default function Home() {
  const [person, setPerson] = useState<File | null>(null);
  const [qr, setQr] = useState<File | null>(null);
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);

  // Idhellaam Step 9-la backend response-la irundhu set aagum.
  // Ippo backend illa, adhunaala null / idle-la irukkum (fake data illa).
  const [resultUrl] = useState<string | null>(null);
  const [validation] = useState<ValidationStatus>("idle");
  const [progress] = useState<number | null>(null);

  const ready = !!person && !!qr;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2 font-bold">
            <ScanFace className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            Face QR Studio
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-12 px-4 py-10">
        {/* 1. Hero */}
        <section className="text-center">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            Turn Your Face Into a{" "}
            <span className="bg-gradient-to-r from-indigo-600 to-violet-500 bg-clip-text text-transparent">
              Scannable QR Code
            </span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-slate-600 dark:text-slate-400">
            Un photo + payment QR upload pannunga. Face, QR modules-aale form
            aagum. Thooraththula paartha face theriyum, scan pannina payment
            QR work aagum.
          </p>
          <p className="mx-auto mt-4 inline-flex items-center gap-2 rounded-full bg-emerald-50 px-4 py-2 text-sm text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
            <ShieldCheck className="h-4 w-4" />
            Un photos permanent-a store aagaadhu. Temporary-a mattum process
            aagum.
          </p>
        </section>

        {/* 2 + 3. Uploads */}
        <section>
          <Step n={1} title="Photo & Payment QR upload" />
          <div className="grid gap-5 md:grid-cols-2">
            <UploadCard
              title="Person photo"
              hint="JPG, PNG, WEBP · Max 10 MB"
              icon={<ScanFace className="h-5 w-5" />}
              allowedTypes={PERSON_TYPES}
              maxMB={10}
              file={person}
              onFileChange={setPerson}
            />
            <UploadCard
              title="Payment QR"
              hint="JPG, PNG · Max 5 MB (GPay / PhonePe / Paytm / any QR)"
              icon={<QrCode className="h-5 w-5" />}
              allowedTypes={QR_TYPES}
              maxMB={5}
              file={qr}
              onFileChange={setQr}
            />
          </div>
        </section>

        {/* 4. Style customization */}
        <section>
          <Step n={2} title="Style customization" />
          <StyleOptions settings={settings} onChange={setSettings} />
        </section>

        {/* 5. Generate */}
        <section>
          <Step n={3} title="Generate" />
          <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <ul className="space-y-2">
              <CheckItem ok={!!person} text="Person photo upload aachu" />
              <CheckItem ok={!!qr} text="Payment QR upload aachu" />
            </ul>
            <button
              disabled
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Sparkles className="h-4 w-4" /> Generate Face QR
            </button>
            <p className="text-xs text-slate-500">
              {ready
                ? "Rendu files-um ready. Generation engine Step 7-9-la connect aagum, apo dhaan indha button work aagum."
                : "Mudhalla rendu images-um upload pannunga."}
            </p>
          </div>
        </section>

        {/* 6 + 7. Before/After + Validation */}
        <section>
          <Step n={4} title="Preview & validation" />
          <ResultPreview
            personFile={person}
            resultUrl={resultUrl}
            validation={validation}
            progress={progress}
          />
        </section>

        {/* 8. Downloads */}
        <section>
          <Step n={5} title="Download" />
          <DownloadPanel
            resultUrl={resultUrl}
            validation={validation}
            resolution={settings.resolution}
            onResolutionChange={(r) => setSettings({ ...settings, resolution: r })}
            qrFile={qr}
          />
        </section>
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-sm text-slate-500 dark:border-slate-800">
        Face QR Studio · Photos server-la store aagaadhu
      </footer>
    </div>
  );
}