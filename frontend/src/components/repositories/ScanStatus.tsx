"use client";

import { useEffect, useState } from "react";
import { Loader2, CheckCircle2, XCircle, Clock, Wifi } from "lucide-react";
import { cn } from "@/lib/utils";
import { repositoriesApi } from "@/lib/api/repositories";
import type { ScanJob } from "@/types/repository";

const STAGE_LABELS: Record<string, string> = {
  fetching_tree:  "Fetching file tree…",
  downloading:    "Downloading files…",
  analyzing:      "Analyzing code…",
  building_graph: "Building architecture graph…",
  scoring:        "Computing metrics…",
  done:           "Complete",
  // legacy labels
  cloning:        "Cloning repository…",
  building_graph2:"Building architecture graph…",
};

const STAGE_PROGRESS: Record<string, number> = {
  fetching_tree:  15,
  downloading:    35,
  analyzing:      60,
  building_graph: 80,
  scoring:        90,
  done:           100,
  cloning:        20,
};

interface ScanStatusProps {
  repoId: string;
  initialJob: ScanJob;
  onComplete?: (job: ScanJob) => void;
}

export function ScanStatus({ repoId, initialJob, onComplete }: ScanStatusProps) {
  const [job, setJob] = useState<ScanJob>(initialJob);
  const [useSSE, setUseSSE] = useState(true);

  useEffect(() => {
    if (job.status !== "running" && job.status !== "pending") return;

    // Try SSE first for real-time updates
    if (useSSE && typeof EventSource !== "undefined") {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      // Get token from localStorage
      let token = "";
      try {
        const raw = localStorage.getItem("lam_auth");
        if (raw) token = JSON.parse(raw)?.state?.token || "";
      } catch { /* ignore */ }

      // SSE doesn't support headers natively — fall back to polling for auth
      // Use polling which works everywhere
      setUseSSE(false);
    }

    // Polling fallback (works reliably with auth)
    const interval = setInterval(async () => {
      try {
        const scans = await repositoriesApi.listScans(repoId);
        const latest = scans[0];
        if (latest) {
          setJob(latest);
          if (latest.status === "completed" || latest.status === "failed") {
            clearInterval(interval);
            onComplete?.(latest);
          }
        }
      } catch {
        clearInterval(interval);
      }
    }, 1500);   // 1.5s polling — fast enough for good UX

    return () => clearInterval(interval);
  }, [job.status, repoId, onComplete, useSSE]);

  const progress = STAGE_PROGRESS[job.stage ?? ""] ?? 0;
  const stageLabel = STAGE_LABELS[job.stage ?? ""] ?? "Running…";

  if (job.status === "pending") return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <Clock className="w-3.5 h-3.5 shrink-0" />
      <span>Queued…</span>
    </div>
  );

  if (job.status === "running") return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-primary">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span className="font-medium">{stageLabel}</span>
        </div>
        <span className="text-muted-foreground">{progress}%</span>
      </div>
      <div className="h-1 rounded-full bg-secondary/60 overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all duration-700"
          style={{ width: `${progress}%`, boxShadow: "0 0 8px hsl(var(--primary))" }}
        />
      </div>
      {job.files_scanned > 0 && (
        <p className="text-xs text-muted-foreground">{job.files_scanned} files analyzed</p>
      )}
    </div>
  );

  if (job.status === "completed") return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-medium">
        <CheckCircle2 className="w-3.5 h-3.5" />
        <span>Scan complete</span>
      </div>
      <div className="flex gap-3 text-xs text-muted-foreground">
        <span>{job.files_scanned} files</span>
        {job.nodes_created > 0 && <span>{job.nodes_created} nodes</span>}
        {job.edges_created > 0 && <span>{job.edges_created} edges</span>}
      </div>
    </div>
  );

  if (job.status === "failed") return (
    <div className="space-y-1">
      <div className="flex items-center gap-1.5 text-red-400 text-xs font-medium">
        <XCircle className="w-3.5 h-3.5" />
        <span>Scan failed</span>
      </div>
      {job.error_message && (
        <p className="text-xs text-muted-foreground line-clamp-2">{job.error_message}</p>
      )}
    </div>
  );

  return null;
}
