"use client";

import { useState } from "react";
import Link from "next/link";
import { GitBranch, Star, Globe, Lock, Play, Trash2, Share2, BarChart2, MessageSquare, ExternalLink, Loader2, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { ScanStatus } from "./ScanStatus";
import type { Repository, ScanJob } from "@/types/repository";

interface RepoCardProps {
  repo: Repository;
  onScan: (id: string) => Promise<ScanJob>;
  onDelete: (id: string) => Promise<void>;
}

const LANG_COLORS: Record<string, string> = {
  Python: "bg-blue-500", TypeScript: "bg-blue-400", JavaScript: "bg-yellow-400",
  Java: "bg-orange-500", Go: "bg-cyan-400", Rust: "bg-orange-400", "C#": "bg-purple-500", Ruby: "bg-red-400",
};

export function RepoCard({ repo, onScan, onDelete }: RepoCardProps) {
  const [scanning, setScanning]   = useState(false);
  const [activeJob, setActiveJob] = useState<ScanJob | null>(repo.latest_scan ?? null);
  const [deleting, setDeleting]   = useState(false);

  const handleScan = async () => {
    setScanning(true);
    try { const job = await onScan(repo.id); setActiveJob(job); }
    catch { /* handled by parent */ }
    finally { setScanning(false); }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete "${repo.name}"? This cannot be undone.`)) return;
    setDeleting(true);
    try { await onDelete(repo.id); } finally { setDeleting(false); }
  };

  const isRunning = activeJob?.status === "running" || activeJob?.status === "pending";
  const isScanned = activeJob?.status === "completed";

  return (
    <div className="group relative rounded-2xl border border-border/60 bg-card/60 p-5 space-y-4 hover:border-primary/30 hover:bg-card transition-all">
      {/* Top highlight line on hover */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-t-2xl" />

      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            {repo.is_private
              ? <Lock className="w-3 h-3 text-muted-foreground/60 shrink-0" />
              : <Globe className="w-3 h-3 text-muted-foreground/60 shrink-0" />}
            <a href={repo.github_url} target="_blank" rel="noopener noreferrer"
              className="font-semibold text-sm hover:text-primary transition-colors truncate flex items-center gap-1">
              {repo.full_name}
              <ExternalLink className="w-3 h-3 shrink-0 opacity-0 group-hover:opacity-60 transition-opacity" />
            </a>
          </div>
          {repo.description && (
            <p className="text-xs text-muted-foreground mt-1.5 line-clamp-2 leading-relaxed">{repo.description}</p>
          )}
        </div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground/60 shrink-0 bg-secondary/50 px-2 py-1 rounded-lg">
          <Star className="w-3 h-3" />
          <span>{repo.star_count.toLocaleString()}</span>
        </div>
      </div>

      {/* Language + framework badges */}
      {(repo.languages.length > 0 || repo.frameworks.length > 0) && (
        <div className="flex flex-wrap gap-1.5">
          {repo.languages.slice(0, 4).map(lang => (
            <span key={lang} className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg bg-secondary/60 border border-border/40">
              <span className={cn("w-2 h-2 rounded-full shrink-0", LANG_COLORS[lang] ?? "bg-gray-400")} />
              {lang}
            </span>
          ))}
          {repo.frameworks.slice(0, 3).map(fw => (
            <span key={fw} className="text-xs px-2.5 py-1 rounded-lg border border-primary/20 text-primary/70 bg-primary/5">
              {fw}
            </span>
          ))}
        </div>
      )}

      {/* Scan status */}
      {activeJob && (
        <div className="rounded-xl bg-secondary/40 border border-border/40 px-3 py-2">
          <ScanStatus repoId={repo.id} initialJob={activeJob} onComplete={setActiveJob} />
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-1 border-t border-border/40">
        <div className="flex items-center gap-1">
          {isScanned && (
            <>
              <Link href={`/graph/${repo.id}`}
                className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg hover:bg-secondary/80 hover:text-primary transition-colors text-muted-foreground">
                <Share2 className="w-3.5 h-3.5" />Graph
              </Link>
              <Link href={`/analytics/${repo.id}`}
                className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg hover:bg-secondary/80 hover:text-emerald-400 transition-colors text-muted-foreground">
                <BarChart2 className="w-3.5 h-3.5" />Analytics
              </Link>
              <Link href={`/copilot/${repo.id}`}
                className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg hover:bg-secondary/80 hover:text-violet-400 transition-colors text-muted-foreground">
                <MessageSquare className="w-3.5 h-3.5" />Copilot
              </Link>
            </>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <button onClick={handleScan} disabled={isRunning || scanning}
            className={cn(
              "inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-medium transition-all",
              isRunning ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" : "bg-primary/10 text-primary border border-primary/20 hover:bg-primary hover:text-primary-foreground hover:glow-sm",
              "disabled:opacity-50"
            )}>
            {isRunning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
            {isRunning ? "Scanning…" : isScanned ? "Re-scan" : "Scan"}
          </button>
          <button onClick={handleDelete} disabled={deleting || isRunning}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-400/10 disabled:opacity-50 transition-all"
            title="Delete">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
