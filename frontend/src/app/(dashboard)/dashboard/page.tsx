"use client";

import Link from "next/link";
import { GitBranch, Share2, BarChart2, MessageSquare, Plus, ArrowRight, Zap, TrendingUp, Activity } from "lucide-react";
import { useRepositories } from "@/hooks/useRepositories";
import { useAuthStore } from "@/lib/store/authStore";

export default function DashboardPage() {
  const { repositories, loading } = useRepositories();
  const { user } = useAuthStore();

  const scanned  = repositories.filter(r => r.latest_scan?.status === "completed");
  const scanning = repositories.filter(r => r.latest_scan?.status === "running" || r.latest_scan?.status === "pending");

  const stats = [
    { label: "Repositories",  value: repositories.length, icon: GitBranch,   color: "from-blue-500/20 to-blue-600/5",   iconColor: "text-blue-400",   href: "/repositories" },
    { label: "Scanned",        value: scanned.length,      icon: TrendingUp,  color: "from-emerald-500/20 to-emerald-600/5", iconColor: "text-emerald-400", href: "/repositories" },
    { label: "In Progress",    value: scanning.length,     icon: Activity,    color: "from-amber-500/20 to-amber-600/5",  iconColor: "text-amber-400",  href: "/repositories" },
  ];

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero greeting */}
      <div className="relative rounded-2xl overflow-hidden border border-border/60 bg-gradient-to-br from-primary/10 via-card to-card p-6">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
        <div className="relative">
          <p className="text-sm text-muted-foreground">{greeting}{user?.name ? `, ${user.name.split(" ")[0]}` : ""} 👋</p>
          <h2 className="text-2xl font-bold mt-1">
            {repositories.length === 0 ? "Let's analyze your first repository" : "Your architecture overview"}
          </h2>
          <p className="text-sm text-muted-foreground mt-2 max-w-xl">
            Connect a GitHub repository to automatically analyze its architecture, visualize dependencies, and get AI-powered insights.
          </p>
          {repositories.length === 0 && (
            <Link href="/repositories"
              className="inline-flex items-center gap-2 mt-4 rounded-xl bg-primary text-primary-foreground px-4 py-2.5 text-sm font-semibold hover:opacity-90 transition-all glow-sm">
              <Plus className="w-4 h-4" /> Add first repository
            </Link>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-3">
        {stats.map(({ label, value, icon: Icon, color, iconColor, href }) => (
          <Link key={label} href={href}
            className="relative rounded-2xl border border-border/60 bg-card p-5 overflow-hidden hover:border-primary/30 transition-all group">
            <div className={`absolute inset-0 bg-gradient-to-br ${color} opacity-60 group-hover:opacity-100 transition-opacity`} />
            <div className="relative">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm text-muted-foreground">{label}</p>
                <Icon className={`w-4 h-4 ${iconColor}`} />
              </div>
              <p className="text-3xl font-bold">
                {loading ? <span className="skeleton inline-block w-8 h-7 rounded" /> : value}
              </p>
            </div>
          </Link>
        ))}
      </div>

      {/* Recent repos */}
      {repositories.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Recent Repositories</h3>
            <Link href="/repositories" className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1 transition-colors">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="space-y-2">
            {repositories.slice(0, 5).map(repo => (
              <div key={repo.id}
                className="flex items-center justify-between rounded-xl border border-border/60 bg-card/60 px-4 py-3 hover:border-primary/20 hover:bg-card transition-all">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-secondary/80 flex items-center justify-center shrink-0">
                    <GitBranch className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{repo.full_name}</p>
                    <p className="text-xs text-muted-foreground truncate">
                      {repo.languages.slice(0, 3).join(" · ") || "No languages detected"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 shrink-0 ml-4">
                  {repo.latest_scan?.status === "completed" ? (
                    <>
                      <Link href={`/graph/${repo.id}`} title="Graph" className="p-1.5 rounded-lg hover:bg-secondary/80 transition-colors text-muted-foreground hover:text-primary"><Share2 className="w-3.5 h-3.5" /></Link>
                      <Link href={`/analytics/${repo.id}`} title="Analytics" className="p-1.5 rounded-lg hover:bg-secondary/80 transition-colors text-muted-foreground hover:text-emerald-400"><BarChart2 className="w-3.5 h-3.5" /></Link>
                      <Link href={`/copilot/${repo.id}`} title="Copilot" className="p-1.5 rounded-lg hover:bg-secondary/80 transition-colors text-muted-foreground hover:text-violet-400"><MessageSquare className="w-3.5 h-3.5" /></Link>
                    </>
                  ) : repo.latest_scan?.status === "running" ? (
                    <span className="text-xs text-amber-400 flex items-center gap-1 animate-pulse">
                      <Zap className="w-3 h-3" /> Scanning
                    </span>
                  ) : (
                    <span className="text-xs text-muted-foreground">Not scanned</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
