// Style, settings, status types. Backend-ku anuppura values-um idhu dhaan.

export type StyleId = "face" | "portrait" | "minimal";
export type Resolution = 1024 | 2048 | 4096;
export type ValidationStatus = "idle" | "verified" | "failed";

export interface Settings {
  style: StyleId;
  qrColor: string; // hex, example "#000000"
  bgColor: string; // hex, example "#ffffff"
  faceVisibility: number; // 0-100
  density: number; // 0-100 (QR pattern density)
  contrast: number; // 0-100 (image contrast)
  resolution: Resolution;
}

export const DEFAULT_SETTINGS: Settings = {
  style: "face",
  qrColor: "#000000",
  bgColor: "#ffffff",
  faceVisibility: 70,
  density: 50,
  contrast: 50,
  resolution: 2048,
};

export const STYLES: { id: StyleId; name: string; desc: string }[] = [
  {
    id: "face",
    name: "Face QR",
    desc: "QR modules person-oda face-a form pannum.",
  },
  {
    id: "portrait",
    name: "Portrait QR",
    desc: "Face details QR pattern-oda blend aagum.",
  },
  {
    id: "minimal",
    name: "Minimal QR",
    desc: "Clean QR, subtle facial artwork.",
  },
];

export const RESOLUTIONS: Resolution[] = [1024, 2048, 4096];