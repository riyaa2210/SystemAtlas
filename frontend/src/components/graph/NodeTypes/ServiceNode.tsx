"use client";
import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Server } from "lucide-react";

export const ServiceNode = memo(({ data, selected }: NodeProps) => (
  <div className={`px-3 py-2 rounded-lg border-2 bg-blue-950 min-w-[120px] text-center transition-all ${selected ? "border-blue-400 shadow-lg shadow-blue-400/20" : "border-blue-700"}`}>
    <Handle type="target" position={Position.Top} className="!bg-blue-400" />
    <div className="flex items-center justify-center gap-1.5 mb-1">
      <Server className="w-3.5 h-3.5 text-blue-400" />
      <span className="text-xs font-semibold text-blue-300">Service</span>
    </div>
    <p className="text-xs text-white font-medium truncate max-w-[140px]">{String(data.label)}</p>
    <Handle type="source" position={Position.Bottom} className="!bg-blue-400" />
  </div>
));
ServiceNode.displayName = "ServiceNode";
