// Upload panna file type + size check panra function.
// Error irundha message return pannum, sariyaa irundha null return pannum.

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
    return `Idhu support aagadha file type. Allowed: ${names}`;
  }
  if (file.size > maxMB * 1024 * 1024) {
    return `File romba periyadhu. Max size ${maxMB} MB.`;
  }
  if (file.size === 0) {
    return "File empty-a irukku.";
  }
  return null;
}