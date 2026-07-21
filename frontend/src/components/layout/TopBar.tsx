"use client";

import { usePathname } from "next/navigation";
import { useAuthStore } from "@/lib/store/authStore";
import { Cpu } from "lucide-react";

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/dashboard":    { title: "Dashboard",    subtitle: "Overview of your repositories" },
  "/repositories": { title: "Repositories", subtitle: "Manage and scan your codebases" },
  "/settings":     { title: "Settings",     subtitle: "Account and preferences" },
};

export function TopBar() {
  const { user } = useAuthStore();
  const pathname = usePathname();

  const base = "/" + pathname.split("/")[1];
  const meta = PAGE_TITLES[base] ?? { title: "Living Architecture Map", subtitle: "" };

  return (
    <header className="h-14 border-b border-border/60 px-6 flex items-center justify-between shrink-0 bg-card/30 backdrop-blur-sm">
      <div>
        <h1 className="text-sm font-semibold leading-none">{meta.title}</h1>
        {meta.subtitle && <p className="text-xs text-muted-foreground mt-0.5">{meta.subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        {/* Status indicator */}
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground bg-secondary/50 px-2.5 py-1 rounded-full border border-border/60">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Live
        </div>

        {/* User avatar */}
        {user && (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center">
              <span className="text-xs font-bold text-primary">{user.name[0].toUpperCase()}</span>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
