"use client";

import Link from "next/link";
import { use } from "react";
import { FileCode, Share2, GitBranch, AlertTriangle, BookOpen, RefreshCw, ArrowLeft } from "lucide-react";
import { useAnalytics } from "@/hooks/useAnalytics";
import { ArchitectureScore } from "@/components/analytics/ArchitectureScore";
import { MetricCard } from "@/components/analytics/MetricCard";
import { RiskList } from "@/components/analytics/RiskList";

export default function AnalyticsPage({ params }: { params: Promise<{ repoId: string }> }) {
  const { repoId } = use(params);
  const { analytics, risks, loading, error, refresh } = useAnalytics(repoId);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link href="/repositories" className="text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="w-4 h-4" /></Link>
            <h2 className="text-2xl font-bold tracking-tight">Architecture Analytics</h2>
          </div>
          <p className="text-muted-foreground text-sm">Architecture health metrics and risk analysis.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={refresh} className="p-2 rounded-md hover:bg-secondary transition-colors text-muted-foreground" title="Refresh">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <Link href={`/graph/${repoId}`} className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm hover:bg-secondary transition-colors">
            <Share2 className="w-4 h-4" /> View Graph
          </Link>
          <Link href={`/copilot/${repoId}`} className="inline-flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm hover:opacity-90 transition-opacity">
            Ask AI
          </Link>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
          <p>{error}</p>
          <Link href="/repositories" className="text-sm text-primary hover:underline mt-2 inline-block">Go to Repositories →</Link>
        </div>
      )}

      {loading && (
        <div className="space-y-6">
          <div className="h-40 rounded-lg border bg-card animate-pulse" />
          <div className="grid gap-4 sm:grid-cols-4">{[1,2,3,4].map(i => <div key={i} className="h-28 rounded-lg border bg-card animate-pulse" />)}</div>
        </div>
      )}

      {analytics && !loading && (
        <>
          <div className="grid gap-6 lg:grid-cols-[auto_1fr]">
            <div className="rounded-xl border bg-card p-6 flex items-center justify-center">
              <ArchitectureScore score={analytics.architecture_score} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <MetricCard label="Total Files"        value={analytics.total_files}        icon={FileCode}  description="Analyzed source files" />
              <MetricCard label="Total Modules"      value={analytics.total_modules}      icon={GitBranch} description="Top-level code modules" />
              <MetricCard label="Total Dependencies" value={analytics.total_dependencies} icon={Share2}    description="Dependency edges in graph" />
              <MetricCard label="Missing Docs"       value={analytics.missing_docs}       icon={BookOpen}  description="Files without documentation" variant={analytics.missing_docs > 5 ? "warning" : "default"} />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <MetricCard label="Circular Dependencies" value={analytics.circular_deps}  icon={AlertTriangle} variant={analytics.circular_deps > 0 ? "danger" : "success"} description={analytics.circular_deps > 0 ? "Cycles detected" : "No cycles"} />
            <MetricCard label="Highly Coupled"        value={analytics.highly_coupled} icon={AlertTriangle} variant={analytics.highly_coupled > 0 ? "warning" : "success"} description={analytics.highly_coupled > 0 ? "Too many dependencies" : "Coupling healthy"} />
            <MetricCard label="Dead Modules"          value={analytics.dead_modules}   icon={AlertTriangle} variant={analytics.dead_modules > 0 ? "warning" : "success"} description={analytics.dead_modules > 0 ? "Possibly unused" : "None found"} />
          </div>

          <div>
            <h3 className="font-semibold mb-3">Risk Details</h3>
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
        </>
      )}
    </div>
  );
}
