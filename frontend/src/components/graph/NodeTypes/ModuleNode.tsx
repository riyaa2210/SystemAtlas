"use client";
import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Package } from "lucide-react";

export const ModuleNode = memo(({ data, selected }: NodeProps) => (
  <div className={`px-3 py-2 rounded-lg border-2 bg-purple-950 min-w-[120px] text-center transition-all ${selected ? "border-purple-400 shadow-lg shadow-purple-400/20" : "border-purple-700"}`}>
    <Handle type="target" position={Position.Top} className="!bg-purple-400" />
    <div className="flex items-center justify-center gap-1.5 mb-1">
      <Package className="w-3.5 h-3.5 text-purple-400" />
      <span className="text-xs font-semibold text-purple-300">Module</span>
    </div>
    <p className="text-xs text-white font-medium truncate max-w-[140px]">{String(data.label)}</p>
    <Handle type="source" position={Position.Bottom} className="!bg-purple-400" />
  </div>
));
ModuleNode.displayName = "ModuleNode";
