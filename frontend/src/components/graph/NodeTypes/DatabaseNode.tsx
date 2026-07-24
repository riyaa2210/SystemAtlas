"use client";
import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Database } from "lucide-react";

export const DatabaseNode = memo(({ data, selected }: NodeProps) => (
  <div className={`px-3 py-2 rounded-lg border-2 bg-red-950 min-w-[120px] text-center transition-all ${selected ? "border-red-400 shadow-lg shadow-red-400/20" : "border-red-800"}`}>
    <Handle type="target" position={Position.Top} className="!bg-red-400" />
    <div className="flex items-center justify-center gap-1.5 mb-1">
      <Database className="w-3.5 h-3.5 text-red-400" />
      <span className="text-xs font-semibold text-red-300">Database</span>
    </div>
    <p className="text-xs text-white font-medium truncate max-w-[140px]">{String(data.label)}</p>
    <Handle type="source" position={Position.Bottom} className="!bg-red-400" />
  </div>
));
DatabaseNode.displayName = "DatabaseNode";
