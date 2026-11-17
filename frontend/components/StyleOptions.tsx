"use client";

import { AlertTriangle } from "lucide-react";
import {
  STYLES,
  RESOLUTIONS,
  type Settings,
  type Resolution,
} from "@/lib/types";
import { contrastRatio, isQrDarker } from "@/lib/color";

interface Props {
  settings: Settings;
  onChange: (next: Settings) => void;
}

// Reusable slider
function Slider({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <label className="font-medium">{label}</label>
        <span className="text-slate-500">{value}%</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-indigo-600"
      />
    </div>
  );
}

export default function StyleOptions({ settings, onChange }: Props) {
  const set = <K extends keyof Settings>(key: K, value: Settings[K]) =>
    onChange({ ...settings, [key]: value });

  // Color contrast check: kammiyaa irundha scan aagaadhu
  const ratio = contrastRatio(settings.qrColor, settings.bgColor);
  const darker = isQrDarker(settings.qrColor, settings.bgColor);
  const lowContrast = ratio < 4;

  return (
    <div className="space-y-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      {/* Artistic style */}
      <div>
        <h3 className="mb-3 font-semibold">Artistic Style</h3>
        <div className="grid gap-3 sm:grid-cols-3">
          {STYLES.map((s) => {
            const active = settings.style === s.id;
            return (
              <button
                key={s.id}
                onClick={() => set("style", s.id)}
                className={`rounded-xl border p-4 text-left transition ${
                  active
                    ? "border-indigo-600 bg-indigo-50 ring-2 ring-indigo-600/30 dark:bg-indigo-950/40"
                    : "border-slate-200 hover:border-indigo-300 dark:border-slate-700"
                }`}
              >
                <p className="font-medium">{s.name}</p>
                <p className="mt-1 text-xs text-slate-500">{s.desc}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Colors */}
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-sm dark:border-slate-700">
          <span className="font-medium">QR color</span>
          <span className="flex items-center gap-2">
            <code className="text-xs text-slate-500">{settings.qrColor}</code>
            <input
              type="color"
              value={settings.qrColor}
              onChange={(e) => set("qrColor", e.target.value)}
              className="h-8 w-10 cursor-pointer rounded border-0 bg-transparent"
            />
          </span>
        </label>
        <label className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-sm dark:border-slate-700">
          <span className="font-medium">Background color</span>
          <span className="flex items-center gap-2">
            <code className="text-xs text-slate-500">{settings.bgColor}</code>
            <input
              type="color"
              value={settings.bgColor}
              onChange={(e) => set("bgColor", e.target.value)}
              className="h-8 w-10 cursor-pointer rounded border-0 bg-transparent"
            />
          </span>
        </label>
      </div>

      {(lowContrast || !darker) && (
        <p className="flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          {!darker
            ? "QR color, background-a vida dark-a irukkanum. Illa-na scanner-ku problem varum."
            : `Color contrast kammi (${ratio.toFixed(1)}:1). Scan aaga kurainjadhu 4:1 mela irukkanum.`}
        </p>
      )}

      {/* Sliders */}
      <div className="grid gap-5 sm:grid-cols-3">
        <Slider
          label="Face visibility"
          value={settings.faceVisibility}
          onChange={(v) => set("faceVisibility", v)}
        />
        <Slider
          label="Pattern density"
          value={settings.density}
          onChange={(v) => set("density", v)}
        />
        <Slider
          label="Image contrast"
          value={settings.contrast}
          onChange={(v) => set("contrast", v)}
        />
      </div>

      {/* Output resolution */}
      <div>
        <h3 className="mb-2 text-sm font-semibold">Output resolution</h3>
        <div className="flex flex-wrap gap-2">
          {RESOLUTIONS.map((r: Resolution) => (
            <button
              key={r}
              onClick={() => set("resolution", r)}
              className={`rounded-lg border px-4 py-2 text-sm transition ${
                settings.resolution === r
                  ? "border-indigo-600 bg-indigo-600 text-white"
                  : "border-slate-200 hover:border-indigo-300 dark:border-slate-700"
              }`}
            >
              {r} px
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}