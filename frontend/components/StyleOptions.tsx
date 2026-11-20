"use client";

import { CheckCircle2 } from "lucide-react";
import { STYLES, type Settings } from "@/lib/types";

interface Props {
  settings: Settings;
  onChange: (next: Settings) => void;
}

// User-ku rendu example kaattrom. Onnai click panni choose pannalam.
export default function StyleOptions({ settings, onChange }: Props) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h3 className="mb-1 font-semibold">Style choose pannunga</h3>
      <p className="mb-4 text-sm text-slate-500">
        Un Face QR indha example maari irukkum. Pidichadha click pannunga.
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        {STYLES.map((s) => {
          const active = settings.style === s.id;
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => onChange({ ...settings, style: s.id })}
              aria-pressed={active}
              className={`relative overflow-hidden rounded-xl border-2 text-left transition ${
                active
                  ? "border-indigo-600 ring-2 ring-indigo-600/30"
                  : "border-slate-200 hover:border-indigo-300 dark:border-slate-700"
              }`}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={s.image}
                alt={`${s.name} example`}
                className="aspect-square w-full bg-white object-contain"
              />
              <div className="p-4">
                <p className="flex items-center justify-between font-medium">
                  {s.name}
                  {active && <CheckCircle2 className="h-5 w-5 text-indigo-600" />}
                </p>
                <p className="mt-1 text-xs text-slate-500">{s.desc}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}