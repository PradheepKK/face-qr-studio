"use client";

import { useEffect, useRef, useState } from "react";
import { Link2, Download, Loader2, AlertCircle } from "lucide-react";
import { API_URL } from "@/lib/api";

const SIZE = 2048; // fixed high quality
const DEBOUNCE_MS = 500;

// URL illa-na kaattura blur example QR (decorative, scan aagaadhu)
function PlaceholderQr() {
  const cells: boolean[][] = [];
  let seed = 7;
  for (let r = 0; r < 25; r++) {
    const row: boolean[] = [];
    for (let c = 0; c < 25; c++) {
      seed = (seed * 9301 + 49297) % 233280;
      row.push(seed / 233280 > 0.5);
    }
    cells.push(row);
  }
  const finder = (r: number, c: number) =>
    (r < 7 && c < 7) || (r < 7 && c > 17) || (r > 17 && c < 7);

  return (
    <svg viewBox="0 0 25 25" className="h-full w-full" shapeRendering="crispEdges" aria-hidden>
      {cells.map((row, r) =>
        row.map((on, c) => {
          if (finder(r, c)) return null;
          return on ? <rect key={`${r}-${c}`} x={c} y={r} width={1} height={1} fill="#9ca3af" /> : null;
        })
      )}
      {[
        [0, 0],
        [18, 0],
        [0, 18],
      ].map(([x, y]) => (
        <g key={`${x}-${y}`} fill="#9ca3af">
          <rect x={x} y={y} width={7} height={7} />
          <rect x={x + 1} y={y + 1} width={5} height={5} fill="white" />
          <rect x={x + 2} y={y + 2} width={3} height={3} />
        </g>
      ))}
    </svg>
  );
}

interface QrResult {
  forUrl: string; // endha URL-kku indha result
  blobUrl: string;
  verified: boolean;
}

export default function UrlQrGenerator() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<QrResult | null>(null);
  const [error, setError] = useState<{ forUrl: string; message: string } | null>(null);
  const [pendingFor, setPendingFor] = useState<string | null>(null); // endha URL generate aagudhu
  const resultRef = useRef<QrResult | null>(null);

  const value = url.trim();

  // Derived state: URL maarina pazhaya result/error automatic-a hide aagum
  const shownResult = result && result.forUrl === value ? result : null;
  const shownError = error && error.forUrl === value ? error.message : null;
  const busy = !!value && pendingFor === value;

  // Page poga bodhu blob URL free pannrom
  useEffect(() => {
    return () => {
      if (resultRef.current) URL.revokeObjectURL(resultRef.current.blobUrl);
    };
  }, []);

  // URL maarina 500ms-ku piragu automatic-a generate (setState ellaam async callback-kulla)
  useEffect(() => {
    if (!value) return;

    const ctrl = new AbortController();
    const timer = setTimeout(async () => {
      setPendingFor(value);
      try {
        let res: Response;
        try {
          res = await fetch(`${API_URL}/api/qr/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: value, size: SIZE }),
            signal: ctrl.signal,
          });
        } catch {
          if (ctrl.signal.aborted) return;
          throw new Error(
            "Backend-a connect panna mudiyala. Backend server (port 8000) run aagudha nu paarunga."
          );
        }
        if (!res.ok) {
          let msg = `Server error (${res.status})`;
          try {
            const j = await res.json();
            if (typeof j.detail === "string") msg = j.detail;
          } catch {}
          throw new Error(msg);
        }
        const blob = await res.blob();
        if (ctrl.signal.aborted) return;

        if (resultRef.current) URL.revokeObjectURL(resultRef.current.blobUrl);
        const next: QrResult = {
          forUrl: value,
          blobUrl: URL.createObjectURL(blob),
          verified: res.headers.get("X-QR-Verified") === "verified",
        };
        resultRef.current = next;
        setResult(next);
        setError(null);
      } catch (e) {
        if (ctrl.signal.aborted) return;
        setError({
          forUrl: value,
          message: e instanceof Error ? e.message : "Theriyaadha error.",
        });
      } finally {
        if (!ctrl.signal.aborted) setPendingFor(null);
      }
    }, DEBOUNCE_MS);

    return () => {
      clearTimeout(timer);
      ctrl.abort();
    };
  }, [value]);

  const download = () => {
    if (!shownResult || !shownResult.verified) return;
    const a = document.createElement("a");
    a.href = shownResult.blobUrl;
    a.download = "url-qr.png";
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const canDownload = !!shownResult && shownResult.verified && !busy;

  return (
    <div className="grid gap-8 md:grid-cols-[1fr_320px]">
      {/* Left: URL input */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <label htmlFor="url-input" className="mb-3 flex items-center gap-2 text-base font-semibold">
          <Link2 className="h-4 w-4 text-indigo-600" /> Enter Website URL
        </label>
        <input
          id="url-input"
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          maxLength={500}
          autoComplete="off"
          className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2.5 text-sm outline-none focus:border-indigo-500 dark:border-slate-700"
        />
        <p className="mt-2 text-xs text-slate-500">
          URL type pannunga, QR automatic-a generate aagum. Short link better.
        </p>

        {shownError && (
          <p className="mt-4 flex items-start gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            {shownError}
          </p>
        )}

        {shownResult && !shownResult.verified && !busy && (
          <p className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
            Indha QR scan verify aagala. Download disabled.
          </p>
        )}
      </div>

      {/* Right: preview + download */}
      <div className="space-y-4">
        <div className="relative aspect-square w-full overflow-hidden rounded-3xl border border-slate-200 bg-white p-5 shadow-md dark:border-slate-700">
          {shownResult ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={shownResult.blobUrl} alt="URL QR" className="h-full w-full object-contain" />
          ) : (
            <div className="h-full w-full opacity-60 blur-[3px]">
              <PlaceholderQr />
            </div>
          )}
          {busy && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/60 dark:bg-slate-900/50">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={download}
          disabled={!canDownload}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Download className="h-4 w-4" /> Download QR Code
        </button>
      </div>
    </div>
  );
}