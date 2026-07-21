"use client";
import { use, useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Share2, BarChart2, MessageSquare, Play, Globe, Lock, Star } from "lucide-react";
import { repositoriesApi } from "@/lib/api/repositories";
import { ScanStatus } from "@/components/repositories/ScanStatus";
import type { Repository, ScanJob } from "@/types/repository";

export default function RepositoryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [repo, setRepo] = useState<Repository | null>(null);
  const [activeJob, setActiveJob] = useState<ScanJob | null>(null);
  const [scanning, setScanning] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    repositoriesApi.get(id).then(r => { setRepo(r); setActiveJob(r.latest_scan ?? null); }).finally(() => setLoading(false));
  }, [id]);

  const handleScan = async () => {
    setScanning(true);
    try { const job = await repositoriesApi.triggerScan(id); setActiveJob(job); } finally { setScanning(false); }
  };

  if (loading) return <div className="h-40 rounded-lg border bg-card animate-pulse" />;
  if (!repo) return <p className="text-muted-foreground">Repository not found.</p>;

  const isScanned = activeJob?.status === "completed";
  const isRunning = activeJob?.status === "running" || activeJob?.status === "pending";

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Link href="/repositories" className="text-muted-foreground hover:text-foreground"><ArrowLeft className="w-4 h-4" /></Link>
        <h2 className="text-2xl font-bold tracking-tight">{repo.full_name}</h2>
        {repo.is_private ? <Lock className="w-4 h-4 text-muted-foreground" /> : <Globe className="w-4 h-4 text-muted-foreground" />}
      </div>
      <div className="rounded-xl border bg-card p-6 space-y-4">
        {repo.description && <p className="text-muted-foreground">{repo.description}</p>}
        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1"><Star className="w-4 h-4" />{repo.star_count.toLocaleString()}</span>
          <span>Branch: {repo.default_branch}</span>
          {repo.languages.length > 0 && <span>Languages: {repo.languages.join(", ")}</span>}
          {repo.frameworks.length > 0 && <span>Frameworks: {repo.frameworks.join(", ")}</span>}
        </div>
        {activeJob && <ScanStatus repoId={repo.id} initialJob={activeJob} onComplete={setActiveJob} />}
        <div className="flex flex-wrap gap-2 pt-2">
          <button onClick={handleScan} disabled={isRunning || scanning}
            className="inline-flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm hover:opacity-90 disabled:opacity-50 transition-opacity">
            <Play className="w-4 h-4" />{isRunning ? "Scanning…" : isScanned ? "Re-scan" : "Scan Now"}
          </button>
          {isScanned && <>
            <Link href={`/graph/${repo.id}`} className="inline-flex items-center gap-2 rounded-md border px-4 py-2 text-sm hover:bg-secondary transition-colors"><Share2 className="w-4 h-4" />Graph</Link>
            <Link href={`/analytics/${repo.id}`} className="inline-flex items-center gap-2 rounded-md border px-4 py-2 text-sm hover:bg-secondary transition-colors"><BarChart2 className="w-4 h-4" />Analytics</Link>
            <Link href={`/copilot/${repo.id}`} className="inline-flex items-center gap-2 rounded-md border px-4 py-2 text-sm hover:bg-secondary transition-colors"><MessageSquare className="w-4 h-4" />Copilot</Link>
          </>}
        </div>
      </div>
    </div>
  );
}
