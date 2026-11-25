"use client";

import { ImageIcon, QrCode, Loader2, Check, X } from "lucide-react";
import { usePreviewUrl } from "@/lib/usePreviewUrl";
import type { JobResultMeta } from "@/lib/api";
import type { ValidationStatus } from "@/lib/types";
import ValidationBadge from "./ValidationBadge";

interface Props {
  personFile: File | null;
  resultUrl: string | null;
  validation: ValidationStatus;
  progress: number | null;
  progressMessage: string;
  meta: JobResultMeta | null;
}

export default function ResultPreview({
  personFile,
  resultUrl,
  validation,
  progress,
  progressMessage,
  meta,
}: Props) {
  const beforeUrl = usePreviewUrl(personFile);

  return (
    <div className="space-y-5 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6 dark:border-slate-800 dark:bg-slate-900">
      <div className="grid gap-4 sm:grid-cols-2 sm:gap-6">
        {/* Before */}
        <div>
          <p className="mb-2 text-sm font-medium text-slate-500">Before (original)</p>
          <div className="flex aspect-square items-center justify-center overflow-hidden rounded-xl bg-slate-100 dark:bg-slate-800">
            {beforeUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={beforeUrl} alt="Original" className="h-full w-full object-contain" />
            ) : (
              <div className="text-center text-slate-400">
                <ImageIcon className="mx-auto mb-2 h-10 w-10" />
                <p className="text-sm">Photo upload pannunga</p>
              </div>
            )}
          </div>
        </div>

        {/* After */}
        <div>
          <p className="mb-2 text-sm font-medium text-slate-500">After (Face QR)</p>
          <div className="flex aspect-square items-center justify-center overflow-hidden rounded-xl bg-white ring-1 ring-slate-200 dark:ring-slate-700">
            {resultUrl ? (
              <a href={resultUrl} target="_blank" rel="noreferrer" className="block h-full w-full">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={resultUrl}
                  alt="Face QR"
                  className="h-full w-full cursor-zoom-in object-contain"
                />
              </a>
            ) : (
              <div className="px-4 text-center text-slate-400">
                <QrCode className="mx-auto mb-2 h-10 w-10" />
                <p className="text-sm">Generate pannina piragu inga Face QR varum</p>
              </div>
            )}
          </div>
          {resultUrl && (
            <p className="mt-2 text-xs text-slate-500">Full-size paarka image mela tap pannunga.</p>
          )}
        </div>
      </div>

      {progress !== null && (
        <div className="rounded-xl bg-indigo-50 p-4 dark:bg-indigo-950/30">
          <div className="mb-2 flex items-center justify-between gap-3 text-sm">
            <span className="flex min-w-0 items-center gap-2">
              <Loader2 className="h-4 w-4 shrink-0 animate-spin text-indigo-600" />
              <span className="truncate">{progressMessage}</span>
            </span>
            <span className="font-semibold">{progress}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-indigo-100 dark:bg-slate-700">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-600 to-violet-500 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm font-medium text-slate-500">QR Validation:</span>
        <ValidationBadge status={validation} />
      </div>

      {meta && (
        <div className="space-y-2 text-sm">
          <p
            className={
              meta.verified
                ? "text-emerald-700 dark:text-emerald-300"
                : "text-red-700 dark:text-red-300"
            }
          >
            {meta.message}
          </p>
          <p className="text-xs text-slate-500">
            {meta.summary} · QR version {meta.qr_version} · Level {meta.ec_level} · mask {meta.mask}
          </p>

          <details className="rounded-xl border border-slate-200 p-3 dark:border-slate-700">
            <summary className="cursor-pointer text-xs font-medium text-slate-600 dark:text-slate-300">
              Scan test details
            </summary>

            <div className="mt-3 grid grid-cols-2 gap-1.5 text-xs sm:grid-cols-4">
              {meta.checks.map((c) => (
                <span
                  key={`${c.decoder}-${c.variant}`}
                  className={`inline-flex items-center gap-1 ${
                    c.ok
                      ? "text-emerald-600 dark:text-emerald-400"
                      : c.required
                        ? "text-red-600 dark:text-red-400"
                        : "text-slate-500"
                  }`}
                >
                  {c.ok ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
                  {c.decoder} @ {c.variant}
                  {c.required ? " *" : ""}
                </span>
              ))}
            </div>
            <p className="mt-1 text-[11px] text-slate-500">
              * = required check. Grey fail = advisory mattum.
            </p>

            <ul className="mt-3 space-y-1 text-xs text-slate-500">
              {meta.attempts.map((a) => (
                <li key={a.n}>
                  Attempt {a.n}: version {a.v}, center dot {a.c} →{" "}
                  {a.err ? `error: ${a.err}` : `${a.p}/${a.t} checks${a.ok ? " (verified)" : ""}`}
                </li>
              ))}
            </ul>
          </details>
        </div>
      )}
    </div>
  );
}