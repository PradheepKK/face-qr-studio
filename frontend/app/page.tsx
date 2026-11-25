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

// Section heading (number + title + subtitle)
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
    setProgressMsg("Start aagudhu...");

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
      setError(e instanceof Error ? e.message : "Theriyaadha error nadandhuduchu.");
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
            <Sparkles className="h-3.5 w-3.5" /> Face QR · Real scan verification
          </span>
          <h1 className="mt-5 text-3xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
            Turn Your Face Into a{" "}
            <span className="bg-gradient-to-r from-indigo-600 to-violet-500 bg-clip-text text-transparent">
              Scannable QR Code
            </span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base text-slate-600 sm:text-lg dark:text-slate-400">
            Un photo + payment QR upload pannunga. Face, QR modules-aale form aagum.
            Thooraththula paartha face theriyum, scan pannina payment QR work aagum.
          </p>

          <div className="mt-7 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
            <a
              href="#create"
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-7 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition hover:opacity-95"
            >
              <Sparkles className="h-4 w-4" /> Start creating
            </a>
            <span className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 text-sm text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300">
              <ShieldCheck className="h-4 w-4" /> Photos store aagaadhu
            </span>
          </div>
        </div>
      </section>

      <main className="mx-auto max-w-6xl space-y-14 px-4 pb-16 sm:space-y-16 sm:px-6">
        {/* How it works */}
        <section className="grid gap-4 sm:grid-cols-3">
          <Feature
            icon={<UploadCloud className="h-5 w-5" />}
            title="1. Upload"
            text="Un portrait photo + payment QR (GPay, PhonePe, Paytm, edhuvum)."
          />
          <Feature
            icon={<BadgeCheck className="h-5 w-5" />}
            title="2. Generate + Verify"
            text="Face QR generate aagi, ZXing-la real-a scan test aagum."
          />
          <Feature
            icon={<Download className="h-5 w-5" />}
            title="3. Download HD"
            text="1024 / 2048 / 4096px PNG download pannunga."
          />
        </section>

        <div id="create" className="scroll-mt-24 space-y-14 sm:space-y-16">
          {/* Uploads */}
          <section>
            <Step n={1} title="Upload" subtitle="Rendu images-um venum." />
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

          {/* Style */}
          <section>
            <Step n={2} title="Style" subtitle="Un Face QR indha maari irukkum." />
            <StyleOptions settings={settings} onChange={setSettings} />
          </section>

          {/* Generate */}
          <section>
            <Step n={3} title="Generate" />
            <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6 dark:border-slate-800 dark:bg-slate-900">
              <ul className="space-y-2">
                <CheckItem ok={!!person} text="Person photo upload aachu" />
                <CheckItem ok={!!qr} text="Payment QR upload aachu" />
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
                {generating ? "Generate aagudhu..." : "Generate Face QR"}
              </button>

              {!ready && (
                <p className="text-xs text-slate-500">Mudhalla rendu images-um upload pannunga.</p>
              )}

              {error && (
                <p className="flex items-start gap-2 rounded-xl bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  {error}
                </p>
              )}

              {stale && (
                <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
                  Settings maathitinga. Kaattara image pazhaya settings-oda irukku. Puthusa paarka
                  thirumba Generate pannunga.
                </p>
              )}
            </div>
          </section>

          {/* Preview */}
          <section>
            <Step n={4} title="Preview & validation" />
            <ResultPreview
              personFile={person}
              resultUrl={result?.url ?? null}
              validation={validation}
              progress={progress}
              progressMessage={progressMsg}
              meta={result?.meta ?? null}
            />
          </section>

          {/* Download */}
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