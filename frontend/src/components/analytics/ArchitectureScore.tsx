"use client";

function getScoreConfig(score: number) {
  if (score >= 80) return { color: "text-emerald-400", stroke: "#34d399", bg: "from-emerald-500/20", label: "Excellent" };
  if (score >= 60) return { color: "text-yellow-400",  stroke: "#facc15", bg: "from-yellow-500/20",  label: "Good" };
  if (score >= 40) return { color: "text-orange-400",  stroke: "#fb923c", bg: "from-orange-500/20",  label: "Fair" };
  return              { color: "text-red-400",     stroke: "#f87171", bg: "from-red-500/20",     label: "Poor" };
}

export function ArchitectureScore({ score }: { score: number }) {
  const { color, stroke, bg, label } = getScoreConfig(score);
  const radius = 52;
  const circ   = 2 * Math.PI * radius;
  const offset = circ - (score / 100) * circ;

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative w-40 h-40">
        {/* Glow ring */}
        <div className={`absolute inset-0 rounded-full bg-gradient-to-br ${bg} to-transparent blur-xl opacity-60`} />
        <svg className="w-full h-full -rotate-90 relative" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r={radius} fill="none" stroke="hsl(var(--secondary))" strokeWidth="8" />
          <circle cx="60" cy="60" r={radius} fill="none" stroke={stroke} strokeWidth="8"
            strokeDasharray={circ} strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 6px ${stroke}60)`, transition: "stroke-dashoffset 1s ease" }} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-4xl font-black ${color}`}>{Math.round(score)}</span>
          <span className="text-xs text-muted-foreground font-medium">/100</span>
        </div>
      </div>
      <div className="text-center">
        <p className={`text-lg font-bold ${color}`}>{label}</p>
        <p className="text-xs text-muted-foreground">Architecture Health Score</p>
      </div>
    </div>
  );
}
