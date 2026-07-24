import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  description?: string;
  variant?: "default" | "warning" | "danger" | "success";
}

const VARIANTS = {
  default: { num: "text-foreground",    bg: "from-secondary/60",      border: "border-border/60",    icon: "text-muted-foreground" },
  success: { num: "text-emerald-400",   bg: "from-emerald-500/10",    border: "border-emerald-500/20", icon: "text-emerald-400" },
  warning: { num: "text-yellow-400",    bg: "from-yellow-500/10",     border: "border-yellow-500/20",  icon: "text-yellow-400" },
  danger:  { num: "text-red-400",       bg: "from-red-500/10",        border: "border-red-500/20",     icon: "text-red-400" },
};

export function MetricCard({ label, value, icon: Icon, description, variant = "default" }: MetricCardProps) {
  const v = VARIANTS[variant];
  return (
    <div className={cn("relative rounded-2xl border bg-gradient-to-br to-transparent p-5 overflow-hidden", v.bg, v.border)}>
      <div className="flex items-start justify-between mb-3">
        <p className="text-sm text-muted-foreground font-medium">{label}</p>
        <Icon className={cn("w-4 h-4 shrink-0", v.icon)} />
      </div>
      <p className={cn("text-3xl font-black", v.num)}>{value}</p>
      {description && <p className="text-xs text-muted-foreground mt-2">{description}</p>}
    </div>
  );
}
