"use client";

import { CheckCircle2 } from "lucide-react";
import { STYLES, type Settings } from "@/lib/types";

interface Props {
  settings: Settings;
  onChange: (next: Settings) => void;
}

export default function StyleOptions({ settings, onChange }: Props) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {STYLES.map((s) => {
        const active = settings.style === s.id;
        return (
          <button
            key={s.id}
            type="button"
            onClick={() => onChange({ ...settings, style: s.id })}
            aria-pressed={active}
            className={`flex items-center gap-4 rounded-2xl border-2 bg-white p-3 text-left shadow-sm transition dark:bg-slate-900 ${
              active
                ? "border-indigo-600 ring-4 ring-indigo-600/10"
                : "border-slate-200 hover:border-indigo-300 dark:border-slate-700"
            }`}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={s.image}
              alt={`${s.name} example`}
              className="h-20 w-20 shrink-0 rounded-xl bg-white object-contain sm:h-24 sm:w-24"
            />
            <div className="min-w-0 flex-1">
              <p className="flex items-center justify-between gap-2 font-semibold">
                {s.name}
                {active && <CheckCircle2 className="h-5 w-5 shrink-0 text-indigo-600" />}
              </p>
              <p className="mt-1 text-xs text-slate-500">{s.desc}</p>
            </div>
          </button>
        );
      })}
    </div>
  );
}