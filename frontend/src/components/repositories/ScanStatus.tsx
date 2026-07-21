"use client";

import { useEffect, useState } from "react";
import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { repositoriesApi } from "@/lib/api/repositories";
import type { ScanJob } from "@/types/repository";

const STAGE_LABELS: Record<string, string> = {
  cloning: "Cloning repository…",
  analyzing: "Detecting languages…",
  building_graph: "Building architecture graph…",
  scoring: "Computing metrics…",
  done: "Complete",
};

interface ScanStatusProps {
  repoId: string;
  initialJob: ScanJob;
  onComplete?: (job: ScanJob) => void;
}

export function ScanStatus({ repoId, initialJob, onComplete }: ScanStatusProps) {
  const [job, setJob] = useState<ScanJob>(initialJob);

  // Poll every 2s while running
  useEffect(() => {
    if (job.status !== "running" && job.status !== "pending") return;

    const interval = setInterval(async () => {
      try {
        const updated = await repositoriesApi.getScan(repoId, job.id);
        setJob(updated);
        if (updated.status === "completed" || updated.status === "failed") {
          clearInterval(interval);
          onComplete?.(updated);
        }
      } catch {
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [job.status, job.id, repoId, onComplete]);

  const statusConfig = {
    pending:   { icon: Clock,       color: "text-muted-foreground", label: "Queued" },
    running:   { icon: Loader2,     color: "text-blue-400",         label: STAGE_LABELS[job.stage ?? ""] ?? "Running…" },
    completed: { icon: CheckCircle2,color: "text-green-400",        label: "Scan complete" },
    failed:    { icon: XCircle,     color: "text-destructive",      label: "Scan failed" },
  } as const;

  const config = statusConfig[job.status as keyof typeof statusConfig] ?? statusConfig.pending;
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-2 text-sm">
      <Icon
        className={cn("w-4 h-4 shrink-0", config.color, job.status === "running" && "animate-spin")}
      />
      <span className={config.color}>{config.label}</span>
      {job.status === "completed" && (
        <span className="text-muted-foreground">
          · {job.files_scanned} files · {job.nodes_created} nodes
        </span>
      )}
      {job.status === "failed" && job.error_message && (
        <span className="text-muted-foreground truncate max-w-xs" title={job.error_message}>
          · {job.error_message}
        </span>
      )}
    </div>
  );
}
