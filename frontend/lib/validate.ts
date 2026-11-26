export const PERSON_TYPES = ["image/jpeg", "image/png", "image/webp"];
export const QR_TYPES = ["image/jpeg", "image/png"];

export function validateImage(
  file: File,
  allowedTypes: string[],
  maxMB: number
): string | null {
  if (!allowedTypes.includes(file.type)) {
    const names = allowedTypes
      .map((t) => t.replace("image/", "").toUpperCase())
      .join(", ");
    return `Unsupported file type. Allowed: ${names}`;
  }
  if (file.size > maxMB * 1024 * 1024) {
    return `File is too large. Max size is ${maxMB} MB.`;
  }
  if (file.size === 0) {
    return "The file is empty.";
  }
  return null;
}