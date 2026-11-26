"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  ScanFace,
  QrCode,
  Sparkles,
  ShieldCheck,
  Check,
  Circle,
  Loader2,
  AlertCircle,
  UploadCloud,
  BadgeCheck,
  Download,
} from "lucide-react";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import UploadCard from "@/components/UploadCard";
import StyleOptions from "@/components/StyleOptions";
import ResultPreview from "@/components/ResultPreview";
import DownloadPanel from "@/components/DownloadPanel";
import { runGeneration, type JobResultMeta } from "@/lib/api";
import { PERSON_TYPES, QR_TYPES } from "@/lib/validate";
import { DEFAULT_SETTINGS, type Settings, type ValidationStatus } from "@/lib/types";

function Step({ n, title, subtitle }: { n: number; title: string; subtitle?: string }) {
  return (
    <div className="mb-5 flex items-start gap-3">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-violet-500 text-sm font-semibold text-white shadow-sm">
        {n}
      </span>
      <div>
        <h2 className="text-xl font-bold tracking-tight sm:text-2xl">{title}</h2>
        {subtitle && <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>}
      </div>
    </div>
  );
}

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

function Feature({ icon, title, text }: { icon: ReactNode; title: string; text: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <span className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
        {icon}
      </span>
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-slate-500">{text}</p>
    </div>
  );
}

interface GeneratedResult {
  url: string;
  meta: JobResultMeta;
  settings: Settings;
}

export default function Home() {
  const [person, setPerson] = useState<File | null>(null);
  const [qr, setQr] = useState<File | null>(null);
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);

  const [result, setResult] = useState<GeneratedResult | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [progressMsg, setProgressMsg] = useState("");
  const [error, setError] = useState<string | null>(null);

  const urlRef = useRef<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const generating = progress !== null;
  const ready = !!person && !!qr;

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    };
  }, []);

  const clearResult = () => {
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
    setResult(null);
  };

  const onPersonChange = (f: File | null) => {
    setPerson(f);
    clearResult();
    setError(null);
  };
  const onQrChange = (f: File | null) => {
    setQr(f);
    clearResult();
    setError(null);
  };

  const handleGenerate = async () => {
    if (!person || !qr || generating) return;

    clearResult();
    setError(null);
    setProgress(0);
    setProgressMsg("Starting...");

    const ctrl = new AbortController();
    abortRef.current = ctrl;
    const used = settings;

    try {
      const { blob, meta } = await runGeneration(
        person,
        qr,
        used,
        (p, m) => {
          setProgress(p);
          setProgressMsg(m);
        },
        ctrl.signal
      );
      const url = URL.createObjectURL(blob);
      urlRef.current = url;
      setResult({ url, meta, settings: used });
    } catch (e) {
      if (ctrl.signal.aborted) return;
      setError(e instanceof Error ? e.message : "Something went wrong. Please try again.");
    } finally {
      setProgress(null);
    }
  };

  const validation: ValidationStatus = result
    ? result.meta.verified
      ? "verified"
      : "failed"
    : "idle";

  const stale = !!result && JSON.stringify(result.settings) !== JSON.stringify(settings);

  return (
    <div className="min-h-screen">
      <SiteHeader />

      {/* Hero */}
      <section className="hero-glow">
        <div className="mx-auto max-w-4xl px-4 pb-10 pt-12 text-center sm:px-6 sm:pb-14 sm:pt-20">
          <span className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white/70 px-3 py-1 text-xs font-medium text-indigo-700 backdrop-blur dark:border-indigo-900 dark:bg-slate-900/60 dark:text-indigo-300">
            <Sparkles className="h-3.5 w-3.5" /> Face QR · Scan verified
          </span>
          <h1 className="mt-5 text-3xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
            Turn Your Face Into a{" "}
            <span className="bg-gradient-to-r from-indigo-600 to-violet-500 bg-clip-text text-transparent">
              Scannable QR Code
            </span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base text-slate-600 sm:text-lg dark:text-slate-400">
            Upload your photo and a payment QR. Your face is built from the QR modules
            themselves: it looks like you from a distance and still scans to your payment.
          </p>

          <div className="mt-7 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
            <a
              href="#create"
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-7 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition hover:opacity-95"
            >
              <Sparkles className="h-4 w-4" /> Start creating
            </a>
            <span className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 text-sm text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300">
              <ShieldCheck className="h-4 w-4" /> Your photos are never stored
            </span>
          </div>
        </div>
      </section>

      <main className="mx-auto max-w-6xl space-y-14 px-4 pb-16 sm:space-y-16 sm:px-6">
        <section className="grid gap-4 sm:grid-cols-3">
          <Feature
            icon={<UploadCloud className="h-5 w-5" />}
            title="1. Upload"
            text="Your portrait photo and a payment QR (GPay, PhonePe, Paytm or any QR)."
          />
          <Feature
            icon={<BadgeCheck className="h-5 w-5" />}
            title="2. Generate"
            text="Your Face QR is created and checked to make sure it scans."
          />
          <Feature
            icon={<Download className="h-5 w-5" />}
            title="3. Download"
            text="Get a high-resolution PNG in 1024, 2048 or 4096 px."
          />
        </section>

        <div id="create" className="scroll-mt-24 space-y-14 sm:space-y-16">
          <section>
            <Step n={1} title="Upload" subtitle="Both images are required." />
            <div className="grid gap-4 sm:gap-6 md:grid-cols-2">
              <UploadCard
                title="Person photo"
                hint="JPG, PNG, WEBP · Max 10 MB"
                icon={<ScanFace className="h-5 w-5" />}
                allowedTypes={PERSON_TYPES}
                maxMB={10}
                file={person}
                onFileChange={onPersonChange}
              />
              <UploadCard
                title="Payment QR"
                hint="JPG, PNG · Max 5 MB (GPay / PhonePe / Paytm / any QR)"
                icon={<QrCode className="h-5 w-5" />}
                allowedTypes={QR_TYPES}
                maxMB={5}
                file={qr}
                onFileChange={onQrChange}
              />
            </div>
          </section>

          <section>
            <Step n={2} title="Style" subtitle="Your Face QR will look like this." />
            <StyleOptions settings={settings} onChange={setSettings} />
          </section>

          <section>
            <Step n={3} title="Generate" />
            <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6 dark:border-slate-800 dark:bg-slate-900">
              <ul className="space-y-2">
                <CheckItem ok={!!person} text="Person photo uploaded" />
                <CheckItem ok={!!qr} text="Payment QR uploaded" />
              </ul>

              <button
                type="button"
                onClick={handleGenerate}
                disabled={!ready || generating}
                className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-8 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none sm:w-auto"
              >
                {generating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                {generating ? "Generating..." : "Generate Face QR"}
              </button>

              {!ready && <p className="text-xs text-slate-500">Please upload both images first.</p>}

              {error && (
                <p className="flex items-start gap-2 rounded-xl bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  {error}
                </p>
              )}

              {stale && (
                <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
                  You changed the settings. The image shown uses the old settings. Generate again
                  to update it.
                </p>
              )}
            </div>
          </section>

          <section>
            <Step n={4} title="Preview" />
            <ResultPreview
              personFile={person}
              resultUrl={result?.url ?? null}
              validation={validation}
              progress={progress}
              progressMessage={progressMsg}
              meta={result?.meta ?? null}
            />
          </section>

          <section>
            <Step n={5} title="Download" />
            <DownloadPanel
              onRegenerate={handleGenerate}
              generating={generating}
              resultUrl={result?.url ?? null}
              resultResolution={result?.meta.resolution ?? null}
              validation={validation}
              resolution={settings.resolution}
              onResolutionChange={(r) => setSettings({ ...settings, resolution: r })}
              qrFile={qr}
            />
          </section>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}