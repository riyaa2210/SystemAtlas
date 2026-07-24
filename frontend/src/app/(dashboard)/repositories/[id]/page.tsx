"use client";

import { use, useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, Globe, Lock, GitBranch, Zap, Loader2,
  Share2, Layers, BarChart2, MessageSquare, Settings2,
  FileCode, AlertTriangle, BookOpen, RefreshCw,
  Activity, ExternalLink, Trash2,
} from "lucide-react";
import { repositoriesApi } from "@/lib/api/repositories";
import { ScanStatus } from "@/components/repositories/ScanStatus";
import { ArchitectureGraph } from "@/components/graph/ArchitectureGraph";
import { SystemArchitectureDiagram } from "@/components/architecture/SystemArchitectureDiagram";
import { ChatWindow } from "@/components/copilot/ChatWindow";
import { ArchitectureScore } from "@/components/analytics/ArchitectureScore";
import { MetricCard } from "@/components/analytics/MetricCard";
import { RiskList } from "@/components/analytics/RiskList";
import { useAnalytics } from "@/hooks/useAnalytics";
import { cn } from "@/lib/utils";
import type { Repository, ScanJob } from "@/types/repository";
import { useRouter } from "next/navigation";

// ── Tab definition ────────────────────────────────────────────────────────────

type TabId = "overview" | "graph" | "architecture" | "analytics" | "copilot" | "settings";

interface Tab {
  id: TabId;
  label: string;
  icon: React.FC<{ className?: string }>;
  requiresScan?: boolean;
}

const TABS: Tab[] = [
  { id: "overview",      label: "Overview",      icon: Activity },
  { id: "graph",         label: "Dependency Graph",    icon: Share2,       requiresScan: true },
  { id: "architecture",  label: "System Architecture", icon: Layers,       requiresScan: true },
  { id: "analytics",     label: "Analytics",     icon: BarChart2,    requiresScan: true },
  { id: "copilot",       label: "AI Copilot",    icon: MessageSquare, requiresScan: true },
  { id: "settings",      label: "Settings",      icon: Settings2 },
];

// ── Analytics inline panel ────────────────────────────────────────────────────

function AnalyticsPanel({ repoId }: { repoId: string }) {
  const { analytics, risks, loading, error, refresh } = useAnalytics(repoId);

  if (loading) return (
    <div className="space-y-4 p-1">
      <div className="h-40 rounded-lg border bg-card animate-pulse" />
      <div className="grid gap-4 sm:grid-cols-4">
        {[1,2,3,4].map(i => <div key={i} className="h-28 rounded-lg border bg-card animate-pulse" />)}
      </div>
    </div>
  );

  if (error) return (
    <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground text-sm">
      {error}
    </div>
  );

  if (!analytics) return null;

  return (
    <div className="space-y-6 p-1">
      <div className="grid gap-6 lg:grid-cols-[auto_1fr]">
        <div className="rounded-xl border bg-card p-6 flex items-center justify-center">
          <ArchitectureScore score={analytics.architecture_score} />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <MetricCard label="Total Files"        value={analytics.total_files}        icon={FileCode}  description="Analyzed source files" />
          <MetricCard label="Total Modules"      value={analytics.total_modules}      icon={GitBranch} description="Top-level code modules" />
          <MetricCard label="Total Dependencies" value={analytics.total_dependencies} icon={Share2}    description="Dependency edges in graph" />
          <MetricCard label="Missing Docs"       value={analytics.missing_docs}       icon={BookOpen}  description="Files without documentation"
            variant={analytics.missing_docs > 5 ? "warning" : "default"} />
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <MetricCard label="Circular Dependencies" value={analytics.circular_deps}  icon={AlertTriangle}
          variant={analytics.circular_deps > 0 ? "danger" : "success"}
          description={analytics.circular_deps > 0 ? "Cycles detected" : "No cycles"} />
        <MetricCard label="Highly Coupled"        value={analytics.highly_coupled} icon={AlertTriangle}
          variant={analytics.highly_coupled > 0 ? "warning" : "success"}
          description={analytics.highly_coupled > 0 ? "Too many dependencies" : "Coupling healthy"} />
        <MetricCard label="Dead Modules"          value={analytics.dead_modules}   icon={AlertTriangle}
          variant={analytics.dead_modules > 0 ? "warning" : "success"}
          description={analytics.dead_modules > 0 ? "Possibly unused" : "None found"} />
      </div>
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold">Risk Details</h3>
          <button onClick={refresh} className="p-1.5 rounded-md hover:bg-secondary transition-colors text-muted-foreground" title="Refresh">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
        <RiskList risks={risks} />
      </div>
      {analytics.metrics_json?.score_breakdown && (
        <div className="rounded-xl border bg-card p-5">
          <h3 className="font-semibold mb-4">Score Breakdown</h3>
          <div className="space-y-3">
            {Object.entries(analytics.metrics_json.score_breakdown as Record<string, number>).map(([key, val]) => (
              <div key={key} className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                <span className={val < 0 ? "text-red-400 font-medium" : "font-medium"}>{val > 0 ? `+${val}` : val}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Overview panel ────────────────────────────────────────────────────────────

function OverviewPanel({
  repo,
  activeJob,
  onScan,
  scanning,
}: {
  repo: Repository;
  activeJob: ScanJob | null;
  onScan: () => void;
  scanning: boolean;
}) {
  const isScanned = activeJob?.status === "completed";
  const isRunning = activeJob?.status === "running" || activeJob?.status === "pending";

  const infoItems = [
    { label: "Language",      value: repo.languages.slice(0, 3).join(", ") || "—" },
    { label: "Frameworks",    value: repo.frameworks.slice(0, 3).join(", ") || "—" },
    { label: "Default Branch", value: repo.default_branch },
    { label: "Stars",         value: repo.star_count.toLocaleString() },
    { label: "Status",        value: isScanned ? "Scanned" : isRunning ? "Scanning…" : "Not scanned" },
    { label: "Last Scan",     value: activeJob?.completed_at ? new Date(activeJob.completed_at).toLocaleString() : "—" },
    ...(isScanned ? [
      { label: "Files Analyzed", value: activeJob!.files_scanned.toString() },
      { label: "Nodes",          value: activeJob!.nodes_created.toString() },
      { label: "Edges",          value: activeJob!.edges_created.toString() },
    ] : []),
  ];

  return (
    <div className="space-y-6 p-1">
      {/* Repo meta card */}
      <div className="rounded-xl border bg-card p-6 space-y-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-secondary/60 flex items-center justify-center shrink-0">
            <GitBranch className="w-5 h-5 text-muted-foreground" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-lg leading-tight">{repo.full_name}</h3>
              {repo.is_private
                ? <Lock className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                : <Globe className="w-3.5 h-3.5 text-muted-foreground shrink-0" />}
              <a href={repo.github_url} target="_blank" rel="noopener noreferrer"
                className="text-muted-foreground hover:text-primary transition-colors shrink-0">
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
            {repo.description && (
              <p className="text-sm text-muted-foreground mt-1">{repo.description}</p>
            )}
          </div>
        </div>

        {/* Info grid */}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {infoItems.map(({ label, value }) => (
            <div key={label} className="rounded-lg bg-secondary/40 border border-border/40 px-3 py-2.5">
              <p className="text-[10px] text-muted-foreground/70 uppercase tracking-wider font-medium">{label}</p>
              <p className="text-sm font-medium mt-0.5 truncate">{value}</p>
            </div>
          ))}
        </div>

        {/* Scan status */}
        {activeJob && (
          <div className="rounded-xl bg-secondary/40 border border-border/40 px-3 py-2">
            <ScanStatus repoId={repo.id} initialJob={activeJob} onComplete={() => {}} />
          </div>
        )}
      </div>

      {/* Scan note for unscanned repos */}
      {!isScanned && !isRunning && (
        <div className="rounded-xl border border-dashed border-border/60 p-8 text-center space-y-3">
          <div className="w-10 h-10 rounded-xl bg-secondary/60 flex items-center justify-center mx-auto">
            <Zap className="w-5 h-5 text-muted-foreground" />
          </div>
          <div>
            <p className="font-medium">This repository hasn't been scanned yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              Run a scan to generate the architecture diagram, dependency graph, and analytics.
            </p>
          </div>
          <button onClick={onScan} disabled={scanning}
            className="inline-flex items-center gap-2 rounded-xl bg-primary text-primary-foreground px-5 py-2.5 text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-all">
            {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            Scan Now
          </button>
        </div>
      )}
    </div>
  );
}

// ── Settings panel ────────────────────────────────────────────────────────────

function SettingsPanel({
  repo,
  onScan,
  onDelete,
  scanning,
  isRunning,
}: {
  repo: Repository;
  onScan: () => void;
  onDelete: () => void;
  scanning: boolean;
  isRunning: boolean;
}) {
  return (
    <div className="space-y-4 p-1 max-w-xl">
      <div className="rounded-xl border bg-card p-5 space-y-4">
        <h3 className="font-semibold">Scan Controls</h3>
        <p className="text-sm text-muted-foreground">
          Trigger a new scan to refresh the architecture diagram, dependency graph, and all analytics.
          Previous data is preserved until the new scan completes.
        </p>
        <button onClick={onScan} disabled={scanning || isRunning}
          className="inline-flex items-center gap-2 rounded-xl bg-primary text-primary-foreground px-4 py-2.5 text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-all">
          {scanning || isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
          {isRunning ? "Scanning…" : "Rescan Repository"}
        </button>
      </div>
      <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5 space-y-4">
        <h3 className="font-semibold text-red-400">Danger Zone</h3>
        <p className="text-sm text-muted-foreground">
          Deleting this repository removes all scan data, graphs, and analytics. This cannot be undone.
        </p>
        <button onClick={onDelete}
          className="inline-flex items-center gap-2 rounded-xl border border-red-500/30 text-red-400 px-4 py-2.5 text-sm font-semibold hover:bg-red-500/10 transition-all">
          <Trash2 className="w-4 h-4" />
          Delete Repository
        </button>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

function RepositoryDetailInner({ id }: { id: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [repo, setRepo] = useState<Repository | null>(null);
  const [activeJob, setActiveJob] = useState<ScanJob | null>(null);
  const [scanning, setScanning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  // Honour ?tab=architecture (or any valid tab) from query string
  useEffect(() => {
    const tabParam = searchParams.get("tab") as TabId | null;
    if (tabParam && TABS.some(t => t.id === tabParam)) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  useEffect(() => {
    repositoriesApi.get(id)
      .then(r => { setRepo(r); setActiveJob(r.latest_scan ?? null); })
      .finally(() => setLoading(false));
  }, [id]);

  const handleScan = async () => {
    setScanning(true);
    try {
      const job = await repositoriesApi.triggerScan(id);
      setActiveJob(job);
    } finally {
      setScanning(false);
    }
  };

  const handleDelete = async () => {
    if (!repo || !confirm(`Delete "${repo.name}"? This cannot be undone.`)) return;
    await repositoriesApi.delete(id);
    router.push("/repositories");
  };

  if (loading) return (
    <div className="space-y-4">
      <div className="h-10 w-48 rounded-lg bg-card animate-pulse" />
      <div className="h-64 rounded-xl border bg-card animate-pulse" />
    </div>
  );

  if (!repo) return (
    <div className="flex items-center gap-3 text-muted-foreground">
      <Link href="/repositories"><ArrowLeft className="w-4 h-4" /></Link>
      <p>Repository not found.</p>
    </div>
  );

  const isScanned = activeJob?.status === "completed";
  const isRunning = activeJob?.status === "running" || activeJob?.status === "pending";

  // Tabs that need a scan are disabled if not yet scanned
  const visibleTabs = TABS.filter(t => !t.requiresScan || isScanned || isRunning);

  // Full-height tabs (graph / architecture) need different container sizing
  const isFullHeight = activeTab === "graph" || activeTab === "architecture";

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] gap-4">
      {/* ── Page header ───────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <Link href="/repositories" className="text-muted-foreground hover:text-foreground transition-colors shrink-0">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <h2 className="text-xl font-bold truncate">{repo.full_name}</h2>
          {repo.is_private
            ? <Lock className="w-4 h-4 text-muted-foreground shrink-0" />
            : <Globe className="w-4 h-4 text-muted-foreground shrink-0" />}
        </div>
        {/* Quick action: scan button */}
        <button onClick={handleScan} disabled={isRunning || scanning}
          className={cn(
            "inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-medium transition-all shrink-0",
            isRunning
              ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
              : "bg-primary/10 text-primary border border-primary/20 hover:bg-primary hover:text-primary-foreground",
            "disabled:opacity-50",
          )}>
          {isRunning
            ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
            : <Zap className="w-3.5 h-3.5" />}
          {isRunning ? "Scanning…" : isScanned ? "Rescan" : "Scan"}
        </button>
      </div>

      {/* ── Tab bar ───────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-1 border-b border-border/60 shrink-0 overflow-x-auto pb-px">
        {visibleTabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-t-lg whitespace-nowrap transition-all border-b-2 -mb-px",
                isActive
                  ? "border-primary text-primary bg-primary/5"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:bg-secondary/60",
              )}
            >
              <Icon className="w-3.5 h-3.5 shrink-0" />
              {tab.label}
            </button>
          );
        })}
        {/* Show locked tabs faintly if repo not scanned */}
        {!isScanned && !isRunning && TABS.filter(t => t.requiresScan).map(tab => {
          const Icon = tab.icon;
          return (
            <button key={tab.id} disabled
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-t-lg whitespace-nowrap border-b-2 border-transparent text-muted-foreground/30 cursor-not-allowed -mb-px"
              title="Scan this repository to unlock">
              <Icon className="w-3.5 h-3.5 shrink-0" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ── Tab content ───────────────────────────────────────────────────── */}
      <div className={cn(
        "flex-1 overflow-hidden",
        isFullHeight ? "" : "overflow-y-auto",
      )}>
        {activeTab === "overview" && (
          <OverviewPanel repo={repo} activeJob={activeJob} onScan={handleScan} scanning={scanning} />
        )}

        {activeTab === "graph" && isScanned && (
          <div className="h-full rounded-xl border bg-card overflow-hidden">
            <ArchitectureGraph repoId={repo.id} />
          </div>
        )}

        {activeTab === "architecture" && isScanned && (
          <div className="h-full rounded-xl border bg-card overflow-hidden">
            <SystemArchitectureDiagram repoId={repo.id} />
          </div>
        )}

        {activeTab === "analytics" && isScanned && (
          <AnalyticsPanel repoId={repo.id} />
        )}

        {activeTab === "copilot" && isScanned && (
          <div className="h-full rounded-xl border bg-card p-5">
            <ChatWindow repoId={repo.id} />
          </div>
        )}

        {activeTab === "settings" && (
          <SettingsPanel
            repo={repo}
            onScan={handleScan}
            onDelete={handleDelete}
            scanning={scanning}
            isRunning={isRunning}
          />
        )}
      </div>
    </div>
  );
}

// ── Exported page — wraps inner component in Suspense for useSearchParams ─────

export default function RepositoryDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return (
    <Suspense
      fallback={
        <div className="space-y-4">
          <div className="h-10 w-48 rounded-lg bg-card animate-pulse" />
          <div className="h-64 rounded-xl border bg-card animate-pulse" />
        </div>
      }
    >
      <RepositoryDetailInner id={id} />
    </Suspense>
  );
}
