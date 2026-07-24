"use client";
import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { FileCode } from "lucide-react";

export const FileNode = memo(({ data, selected }: NodeProps) => (
  <div className={`px-3 py-2 rounded-lg border bg-gray-900 min-w-[110px] text-center transition-all ${selected ? "border-green-400 shadow-lg shadow-green-400/20" : "border-gray-700"}`}>
    <Handle type="target" position={Position.Top} className="!bg-gray-400" />
    <div className="flex items-center justify-center gap-1 mb-0.5">
      <FileCode className="w-3 h-3 text-green-400" />
      <span className="text-[10px] text-gray-400">File</span>
    </div>
    <p className="text-[11px] text-gray-200 truncate max-w-[120px]">{String(data.label)}</p>
    <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
  </div>
));
FileNode.displayName = "FileNode";
