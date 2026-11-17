"use client";

import { useEffect, useMemo } from "react";

// File object-a browser-la preview kaattura URL-a maathura hook.
// File maarum bodhu / component poga bodhu old URL-a free pannum (memory leak illa).
export function usePreviewUrl(file: File | null): string | null {
  // File maarina mattum puthu URL create aagum
  const url = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);

  // Old URL-a free pannrom
  useEffect(() => {
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [url]);

  return url;
}