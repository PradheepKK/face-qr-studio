// Backend API client. Job create -> poll progress -> result PNG edukkum.

import type { Settings } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const POLL_MS = 600;

export interface JobCheck {
  decoder: string;
  variant: string;
  ok: boolean;
  required: boolean;
}

export interface JobAttempt {
  n: number;
  v: number;
  c: number;
  ok: boolean;
  p?: number | null;
  t?: number | null;
  err?: string | null;
}

export interface JobResultMeta {
  verified: boolean;
  summary: string;
  message: string;
  checks: JobCheck[];
  attempts: JobAttempt[];
  final_attempt: number;
  qr_version: number;
  mask: number;
  ec_level: string;
  center_frac: number;
  segmentation: string;
  resolution: number;
}

export interface JobStatus {
  job_id: string;
  state: "queued" | "running" | "done" | "error";
  progress: number;
  message: string;
  attempt: number;
  total_attempts: number;
  error: string | null;
  error_status: number | null;
  result: JobResultMeta | null;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

// FastAPI error-la irundhu "detail" message edukkum
async function errorMessage(res: Response): Promise<string> {
  try {
    const j = await res.json();
    if (typeof j.detail === "string") return j.detail;
    if (Array.isArray(j.detail)) {
      return j.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ");
    }
  } catch {
    // JSON illa
  }
  return `Server error (${res.status})`;
}

// fetch wrapper: backend off-na purinjukkura message
async function request(url: string, init?: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(url, init);
  } catch (e) {
    if (e instanceof TypeError) {
      throw new ApiError(
        "Backend-a connect panna mudiyala. Backend server (port 8000) run aagudha nu paarunga.",
        0
      );
    }
    throw e; // AbortError
  }
  if (!res.ok) throw new ApiError(await errorMessage(res), res.status);
  return res;
}

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) return reject(new DOMException("Aborted", "AbortError"));
    const t = setTimeout(resolve, ms);
    signal.addEventListener(
      "abort",
      () => {
        clearTimeout(t);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true }
    );
  });
}

async function createJob(
  person: File,
  qr: File,
  s: Settings,
  signal: AbortSignal
): Promise<string> {
   const fd = new FormData();
  fd.append("person", person);
  fd.append("qr", qr);
  fd.append("style", s.style);
  fd.append("resolution", String(s.resolution));
  const res = await request(`${API_URL}/api/jobs`, { method: "POST", body: fd, signal });
  const data = (await res.json()) as { job_id: string };
  return data.job_id;
}

async function getJob(id: string, signal: AbortSignal): Promise<JobStatus> {
  const res = await request(`${API_URL}/api/jobs/${id}`, { signal });
  return (await res.json()) as JobStatus;
}

async function fetchResult(id: string, signal: AbortSignal): Promise<Blob> {
  const res = await request(`${API_URL}/api/jobs/${id}/result`, { signal });
  return await res.blob();
}

// Main function: generate start pannitu, progress report pannitu, result return pannum
export async function runGeneration(
  person: File,
  qr: File,
  settings: Settings,
  onProgress: (percent: number, message: string) => void,
  signal: AbortSignal
): Promise<{ blob: Blob; meta: JobResultMeta }> {
  const jobId = await createJob(person, qr, settings, signal);
  let failures = 0;

  while (true) {
    await sleep(POLL_MS, signal);

    let st: JobStatus;
    try {
      st = await getJob(jobId, signal);
      failures = 0;
    } catch (e) {
      if (signal.aborted) throw e;
      if (e instanceof ApiError && e.status === 404) {
        throw new ApiError("Job expire aagiduchu. Thirumba Generate pannunga.", 404);
      }
      failures += 1; // oru rendu thadavai network hiccup-na wait pannrom
      if (failures >= 5) throw e;
      continue;
    }

    onProgress(st.progress, st.message);

    if (st.state === "error") {
      throw new ApiError(st.error ?? "Generate fail aachu.", st.error_status ?? 500);
    }
    if (st.state === "done" && st.result) {
      const blob = await fetchResult(jobId, signal);
      return { blob, meta: st.result };
    }
  }
}