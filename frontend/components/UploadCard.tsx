"use client";

import { useRef, useState, type DragEvent, type ReactNode } from "react";
import { UploadCloud, X, CheckCircle2, AlertCircle } from "lucide-react";
import { usePreviewUrl } from "@/lib/usePreviewUrl";
import { validateImage } from "@/lib/validate";

interface Props {
  title: string;
  hint: string;
  icon: ReactNode;
  allowedTypes: string[];
  maxMB: number;
  file: File | null;
  onFileChange: (file: File | null) => void;
}

export default function UploadCard({
  title,
  hint,
  icon,
  allowedTypes,
  maxMB,
  file,
  onFileChange,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const previewUrl = usePreviewUrl(file);

  // File select aanadhum type + size validate pannrom
  const handleFile = (f: File | undefined | null) => {
    if (!f) return;
    const problem = validateImage(f, allowedTypes, maxMB);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    onFileChange(f);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  const remove = () => {
    onFileChange(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4 flex items-center gap-2">
        <span className="text-indigo-600 dark:text-indigo-400">{icon}</span>
        <h3 className="font-semibold">{title}</h3>
      </div>

      {previewUrl && file ? (
        <div className="space-y-3">
          <div className="flex items-center justify-center rounded-xl bg-slate-100 p-3 dark:bg-slate-800">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={previewUrl}
              alt={`${title} preview`}
              className="max-h-64 rounded-lg object-contain"
            />
          </div>
          <div className="flex items-center justify-between gap-2 text-sm">
            <span className="flex min-w-0 items-center gap-2 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span className="truncate">{file.name}</span>
            </span>
            <button
              onClick={remove}
              className="inline-flex shrink-0 items-center gap-1 rounded-lg px-2 py-1 text-slate-500 hover:bg-slate-100 hover:text-red-600 dark:hover:bg-slate-800"
            >
              <X className="h-4 w-4" /> Remove
            </button>
          </div>
          <p className="text-xs text-slate-500">
            {(file.size / 1024).toFixed(0)} KB
          </p>
        </div>
      ) : (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
          }}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-4 py-10 text-center transition ${
            dragging
              ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/40"
              : "border-slate-300 hover:border-indigo-400 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800/50"
          }`}
        >
          <UploadCloud className="mb-3 h-10 w-10 text-slate-400" />
          <p className="text-sm font-medium">
            Drag & drop pannunga, allathu click pannunga
          </p>
          <p className="mt-1 text-xs text-slate-500">{hint}</p>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept={allowedTypes.join(",")}
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />

      {error && (
        <p className="mt-3 flex items-start gap-2 text-sm text-red-600 dark:text-red-400">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </p>
      )}
    </div>
  );
}