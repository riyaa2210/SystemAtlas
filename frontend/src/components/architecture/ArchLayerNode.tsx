"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import {
  Monitor, Server, Shield, Layers, Cpu, Zap, Database,
  HardDrive, Mail, Globe, Brain, Box, CircuitBoard,
} from "lucide-react";

const ICON_MAP: Record<string, React.FC<{ className?: string }>> = {
  monitor:       Monitor,
  server:        Server,
  shield:        Shield,
  layers:        Layers,
  cpu:           Cpu,
  zap:           Zap,
  database:      Database,
  cylinder:      Database,
  "hard-drive":  HardDrive,
  mail:          Mail,
  globe:         Globe,
  brain:         Brain,
  box:           Box,
  "circuit-board": CircuitBoard,
};

export interface ArchLayerNodeData {
  label: string;
  layer: string;
  technologies: string[];
  file_count: number;
  color: string;
  icon: string;
  description: string;
  [key: string]: unknown;
}

export const ArchLayerNode = memo(function ArchLayerNode({
  data,
  selected,
}: NodeProps) {
  const d = data as ArchLayerNodeData;
  const IconComp = ICON_MAP[d.icon] ?? Box;
  const techs = (d.technologies as string[]) ?? [];

  return (
    <div
      className="relative min-w-[240px] max-w-[300px]"
      style={{
        filter: selected ? `drop-shadow(0 0 12px ${d.color}88)` : undefined,
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!w-2 !h-2 !border-2"
        style={{ borderColor: d.color, background: "#0f172a" }}
      />

      {/* Card */}
      <div
        className="rounded-xl border-2 bg-card/90 backdrop-blur-sm px-4 py-3 space-y-2 transition-all"
        style={{ borderColor: selected ? d.color : `${d.color}55` }}
      >
        {/* Header */}
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: `${d.color}22`, border: `1px solid ${d.color}44` }}
          >
            <IconComp className="w-4 h-4" style={{ color: d.color }} />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold leading-tight truncate">{d.label}</p>
            {d.description && (
              <p className="text-[10px] text-muted-foreground/70 truncate">{d.description}</p>
            )}
          </div>
        </div>

        {/* Technology pills */}
        {techs.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {techs.slice(0, 4).map((tech: string) => (
              <span
                key={tech}
                className="text-[10px] px-1.5 py-0.5 rounded-md font-medium"
                style={{ background: `${d.color}18`, color: d.color, border: `1px solid ${d.color}30` }}
              >
                {tech}
              </span>
            ))}
            {techs.length > 4 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-md text-muted-foreground bg-secondary/60">
                +{techs.length - 4}
              </span>
            )}
          </div>
        )}

        {/* File count badge */}
        {d.file_count > 0 && (
          <p className="text-[10px] text-muted-foreground/60">
            {d.file_count} file{d.file_count !== 1 ? "s" : ""}
          </p>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-2 !h-2 !border-2"
        style={{ borderColor: d.color, background: "#0f172a" }}
      />
    </div>
  );
});
