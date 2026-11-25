"use client";

import { Download, QrCode, RefreshCw, Loader2 } from "lucide-react";
import { usePreviewUrl } from "@/lib/usePreviewUrl";
import { RESOLUTIONS, type Resolution, type ValidationStatus } from "@/lib/types";
import ValidationBadge from "./ValidationBadge";

interface Props {
  resultUrl: string | null;
  resultResolution: number | null;
  validation: ValidationStatus;
  resolution: Resolution;
  onResolutionChange: (r: Resolution) => void;
  onRegenerate: () => void;
  generating: boolean;
  qrFile: File | null;
}

function triggerDownload(href: string, filename: string) {
  const a = document.createElement("a");
  a.href = href;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

export default function DownloadPanel({
  resultUrl,
  resultResolution,
  validation,
  resolution,
  onResolutionChange,
  onRegenerate,
  generating,
  qrFile,
}: Props) {
  const qrUrl = usePreviewUrl(qrFile);
  const mismatch = !!resultUrl && resultResolution !== null && resultResolution !== resolution;

  const downloadFaceQr = async () => {
    if (!resultUrl) return;
    const res = await fetch(resultUrl);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    triggerDownload(url, `face-qr-${resultResolution ?? resolution}px.png`);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const downloadOriginalQr = () => {
    if (!qrUrl || !qrFile) return;
    triggerDownload(qrUrl, `original-${qrFile.name}`);
  };

  return (
    <div className="space-y-5 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6 dark:border-slate-800 dark:bg-slate-900">
      <div>
        <p className="mb-2 text-sm font-medium text-slate-500">HD resolution</p>
        <div className="grid grid-cols-3 gap-2 sm:flex">
          {RESOLUTIONS.map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => onResolutionChange(r)}
              className={`min-h-11 rounded-xl border px-4 text-sm font-medium transition ${
                resolution === r
                  ? "border-indigo-600 bg-indigo-600 text-white shadow-sm"
                  : "border-slate-200 hover:border-indigo-300 dark:border-slate-700"
              }`}
            >
              {r} px
            </button>
          ))}
        </div>
        {resultResolution && (
          <p className="mt-2 text-xs text-slate-500">
            Ippo irukkura Face QR: {resultResolution}px
          </p>
        )}
      </div>

      {mismatch && (
        <div className="flex flex-col gap-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-800 sm:flex-row sm:items-center dark:bg-amber-950/40 dark:text-amber-300">
          <span className="flex-1">
            {resolution}px venum-na thirumba generate pannanum (scan verify-um thirumba nadakkum).
          </span>
          <button
            type="button"
            onClick={onRegenerate}
            disabled={generating}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-amber-600 px-4 text-white hover:bg-amber-700 disabled:opacity-50"
          >
            {generating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Regenerate at {resolution}px
          </button>
        </div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <button
          type="button"
          onClick={downloadFaceQr}
          disabled={!resultUrl}
          className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 text-sm font-semibold text-white shadow-sm transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Download className="h-4 w-4" /> Download Face QR (PNG)
        </button>
        <ValidationBadge status={validation} />
      </div>

      <button
        type="button"
        onClick={downloadOriginalQr}
        disabled={!qrFile}
        className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl border border-slate-300 px-6 text-sm font-medium transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 sm:w-auto dark:border-slate-700 dark:hover:bg-slate-800"
      >
        <QrCode className="h-4 w-4" /> Download Original QR
      </button>

      {!resultUrl && (
        <p className="text-xs text-slate-500">
          Face QR download, generate aana piragu enable aagum. Original QR download, QR upload
          pannina udane work aagum.
        </p>
      )}
    </div>
  );
}