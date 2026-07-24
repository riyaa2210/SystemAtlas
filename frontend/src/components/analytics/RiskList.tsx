"use client";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RiskItem } from "@/types/analytics";

const SEVERITY_CONFIG = {
  high:   { icon: AlertTriangle, color: "text-red-400",    bg: "bg-red-400/10",    border: "border-red-400/20" },
  medium: { icon: AlertCircle,   color: "text-yellow-400", bg: "bg-yellow-400/10", border: "border-yellow-400/20" },
  low:    { icon: Info,          color: "text-blue-400",   bg: "bg-blue-400/10",   border: "border-blue-400/20" },
};

interface RiskListProps {
  risks: RiskItem[];
}

export function RiskList({ risks }: RiskListProps) {
  if (risks.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
        No architectural risks detected. Great work!
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {risks.map((risk, i) => {
        const config = SEVERITY_CONFIG[risk.severity] ?? SEVERITY_CONFIG.low;
        const Icon = config.icon;
        return (
          <div key={i} className={cn("rounded-lg border p-4 flex gap-3", config.bg, config.border)}>
            <Icon className={cn("w-5 h-5 shrink-0 mt-0.5", config.color)} />
            <div className="min-w-0">
              <p className="font-medium text-sm">{risk.title}</p>
              <p className="text-xs text-muted-foreground mt-1">{risk.description}</p>
              {risk.affected_nodes.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {risk.affected_nodes.slice(0, 5).map((node, j) => (
                    <span key={j} className="text-xs font-mono bg-secondary px-2 py-0.5 rounded">{node}</span>
                  ))}
                  {risk.affected_nodes.length > 5 && (
                    <span className="text-xs text-muted-foreground">+{risk.affected_nodes.length - 5} more</span>
                  )}
                </div>
              )}
            </div>
            <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full h-fit shrink-0 capitalize border", config.bg, config.border, config.color)}>
              {risk.severity}
            </span>
          </div>
        );
      })}
    </div>
  );
}
