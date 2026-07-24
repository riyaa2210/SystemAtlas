"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, GitBranch, Settings, LogOut, Cpu, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/store/authStore";

const navItems = [
  { href: "/dashboard",    icon: LayoutDashboard, label: "Dashboard" },
  { href: "/repositories", icon: GitBranch,        label: "Repositories" },
];

export function Sidebar() {
  const pathname = usePathname();
  const router   = useRouter();
  const { logout, user } = useAuthStore();

  const handleLogout = () => { logout(); router.push("/login"); };

  return (
    <aside className="w-60 flex flex-col shrink-0 border-r border-border/60 bg-card/50 backdrop-blur-sm">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-border/60">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center group-hover:glow-sm transition-all">
            <Cpu className="w-4 h-4 text-primary" />
          </div>
          <div>
            <p className="font-bold text-sm leading-none">LAM</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">Architecture Map</p>
          </div>
        </Link>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        <p className="text-[10px] font-semibold text-muted-foreground/60 uppercase tracking-widest px-3 pb-2">
          Navigation
        </p>
        {navItems.map(({ href, icon: Icon, label }) => {
          const active = pathname.startsWith(href);
          return (
            <Link key={href} href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-150",
                active
                  ? "bg-primary/10 text-primary font-medium border border-primary/20"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary/80"
              )}>
              <Icon className={cn("w-4 h-4 shrink-0", active && "text-primary")} />
              {label}
              {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary" />}
            </Link>
          );
        })}
      </nav>

      {/* User + bottom actions */}
      <div className="px-3 py-4 space-y-0.5 border-t border-border/60">
        {/* User badge */}
        {user && (
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-secondary/50 mb-2">
            <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
              <span className="text-xs font-bold text-primary">{user.name[0].toUpperCase()}</span>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium truncate">{user.name}</p>
              <p className="text-[10px] text-muted-foreground truncate">{user.email}</p>
            </div>
          </div>
        )}

        <Link href="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/80 transition-all">
          <Settings className="w-4 h-4 shrink-0" />Settings
        </Link>
        <button onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-muted-foreground hover:text-red-400 hover:bg-red-400/10 transition-all">
          <LogOut className="w-4 h-4 shrink-0" />Log out
        </button>
      </div>
    </aside>
  );
}
