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
    <div className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4 flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
          {icon}
        </span>
        <h3 className="font-semibold">{title}</h3>
      </div>

      {previewUrl && file ? (
        <div className="flex flex-1 flex-col gap-3">
          <div className="flex flex-1 items-center justify-center rounded-xl bg-slate-100 p-3 dark:bg-slate-800">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={previewUrl}
              alt={`${title} preview`}
              className="max-h-64 w-full rounded-lg object-contain"
            />
          </div>
          <div className="flex items-center justify-between gap-2 text-sm">
            <span className="flex min-w-0 items-center gap-2 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span className="truncate">{file.name}</span>
              <span className="shrink-0 text-xs text-slate-500">
                {(file.size / 1024).toFixed(0)} KB
              </span>
            </span>
            <button
              type="button"
              onClick={remove}
              className="inline-flex min-h-10 shrink-0 items-center gap-1 rounded-lg px-3 text-slate-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40"
            >
              <X className="h-4 w-4" /> Remove
            </button>
          </div>
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
          className={`flex min-h-52 flex-1 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-4 py-8 text-center transition ${
            dragging
              ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/40"
              : "border-slate-300 hover:border-indigo-400 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800/50"
          }`}
        >
          <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 dark:bg-indigo-950/60">
            <UploadCloud className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
          </span>
          <p className="text-sm font-medium">
            <span className="hidden sm:inline">Drag & drop pannunga, allathu </span>
            <span className="text-indigo-600 dark:text-indigo-400">click / tap pannunga</span>
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