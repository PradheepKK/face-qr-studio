"use client";

import { CheckCircle2 } from "lucide-react";
import { STYLES, type Settings } from "@/lib/types";

interface Props {
  settings: Settings;
  onChange: (next: Settings) => void;
}

// Chinna compact style card(s). Ippo Style 1 mattum.
export default function StyleOptions({ settings, onChange }: Props) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h3 className="mb-3 text-sm font-semibold">Style</h3>

      <div className="flex flex-wrap gap-3">
        {STYLES.map((s) => {
          const active = settings.style === s.id;
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => onChange({ ...settings, style: s.id })}
              aria-pressed={active}
              className={`flex w-full max-w-[420px] items-center gap-4 overflow-hidden rounded-xl border-2 p-2 text-left transition ${
                active
                  ? "border-indigo-600 ring-2 ring-indigo-600/30"
                  : "border-slate-200 hover:border-indigo-300 dark:border-slate-700"
              }`}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={s.image}
                alt={`${s.name} example`}
                className="h-32 w-32 shrink-0 rounded-lg bg-white object-contain"
              />
              <div className="min-w-0 flex-1">
                <p className="flex items-center justify-between gap-2 text-sm font-medium">
                  {s.name}
                  {active && <CheckCircle2 className="h-4 w-4 shrink-0 text-indigo-600" />}
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