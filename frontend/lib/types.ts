// Style + settings types. Backend-ku anuppura values idhu dhaan.

export type StyleId = "halftone" | "pixel";
export type Resolution = 1024 | 2048 | 4096;
export type ValidationStatus = "idle" | "verified" | "failed";

export interface Settings {
  style: StyleId;
  resolution: Resolution;
}

export const DEFAULT_SETTINGS: Settings = {
  style: "halftone",
  resolution: 2048,
};

export const STYLES: {
  id: StyleId;
  name: string;
  desc: string;
  image: string;
}[] = [
  {
    id: "halftone",
    name: "Style 1: Halftone Block",
    desc: "Perusa modules. Hair solid-a, skin-la tone-ku etha dots. Dhooram-la face clear-a theriyum.",
    image: "/styles/style1.jpg",
  },
  {
    id: "pixel",
    name: "Style 2: Fine Pixel",
    desc: "Romba chinna pixel modules. Photo maari detail-a, high-density QR.",
    image: "/styles/style2.jpg",
  },
];

export const RESOLUTIONS: Resolution[] = [1024, 2048, 4096];