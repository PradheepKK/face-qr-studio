"use client";

import { ImageIcon, QrCode } from "lucide-react";
import { usePreviewUrl } from "@/lib/usePreviewUrl";
import ValidationBadge from "./ValidationBadge";
import type { ValidationStatus } from "@/lib/types";

interface Props {
  personFile: File | null;
  resultUrl: string | null;
  validation: ValidationStatus;
  progress: number | null; // null = generate nadakkala
}

export default function ResultPreview({
  personFile,
  resultUrl,
  validation,
  progress,
}: Props) {
  const beforeUrl = usePreviewUrl(personFile);

  return (
    <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="grid gap-4 md:grid-cols-2">
        {/* Before */}
        <div>
          <p className="mb-2 text-sm font-medium text-slate-500">Before (original photo)</p>
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
          <div className="flex aspect-square items-center justify-center overflow-hidden rounded-xl bg-slate-100 dark:bg-slate-800">
            {resultUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={resultUrl} alt="Face QR" className="h-full w-full object-contain" />
            ) : (
              <div className="px-4 text-center text-slate-400">
                <QrCode className="mx-auto mb-2 h-10 w-10" />
                <p className="text-sm">Generate pannina piragu inga Face QR varum</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Progress bar (generate nadakkum bodhu mattum theriyum) */}
      {progress !== null && (
        <div>
          <div className="mb-1 flex justify-between text-sm">
            <span>Generating...</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
            <div
              className="h-full rounded-full bg-indigo-600 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-slate-500">QR Validation:</span>
        <ValidationBadge status={validation} />
      </div>
    </div>
  );
}