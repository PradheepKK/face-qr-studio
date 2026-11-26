import { CheckCircle2, XCircle, Clock } from "lucide-react";
import type { ValidationStatus } from "@/lib/types";

export default function ValidationBadge({ status }: { status: ValidationStatus }) {
  if (status === "verified") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
        <CheckCircle2 className="h-4 w-4" /> Scan Verified
      </span>
    );
  }
  if (status === "failed") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-700 dark:bg-red-950/50 dark:text-red-300">
        <XCircle className="h-4 w-4" /> Scan Failed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
      <Clock className="h-4 w-4" /> Not checked yet
    </span>
  );
}