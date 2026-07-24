"use client";
import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Zap } from "lucide-react";

const METHOD_COLORS: Record<string, string> = { GET: "bg-green-700 text-green-200", POST: "bg-blue-700 text-blue-200", PUT: "bg-yellow-700 text-yellow-200", DELETE: "bg-red-700 text-red-200", PATCH: "bg-orange-700 text-orange-200" };

export const ApiNode = memo(({ data, selected }: NodeProps) => {
  const method = String((data.properties as Record<string, unknown>)?.method || "ANY");
  const colorClass = METHOD_COLORS[method] || "bg-gray-700 text-gray-200";
  return (
    <div className={`px-3 py-2 rounded-lg border-2 bg-amber-950 min-w-[130px] text-center transition-all ${selected ? "border-amber-400 shadow-lg shadow-amber-400/20" : "border-amber-700"}`}>
      <Handle type="target" position={Position.Top} className="!bg-amber-400" />
      <div className="flex items-center justify-center gap-1.5 mb-1">
        <Zap className="w-3.5 h-3.5 text-amber-400" />
        <span className={`text-[10px] font-bold px-1 rounded ${colorClass}`}>{method}</span>
      </div>
      <p className="text-xs text-white font-mono truncate max-w-[140px]">{String(data.label)}</p>
      <Handle type="source" position={Position.Bottom} className="!bg-amber-400" />
    </div>
  );
});
ApiNode.displayName = "ApiNode";
