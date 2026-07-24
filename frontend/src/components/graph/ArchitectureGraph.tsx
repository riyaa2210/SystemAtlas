"use client";

import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow, Background, Controls, MiniMap,
  type Node, type Edge, type NodeTypes,
  useNodesState, useEdgesState, addEdge,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { ServiceNode } from "./NodeTypes/ServiceNode";
import { ModuleNode } from "./NodeTypes/ModuleNode";
import { FileNode } from "./NodeTypes/FileNode";
import { ApiNode } from "./NodeTypes/ApiNode";
import { DatabaseNode } from "./NodeTypes/DatabaseNode";
import { NodeDetailPanel } from "./NodeDetailPanel";
import { useGraph, useNodeDetail } from "@/hooks/useGraph";
import type { GraphNode, GraphEdge } from "@/types/graph";
import { Search, Maximize2 } from "lucide-react";

const nodeTypes: NodeTypes = {
  Service: ServiceNode,
  Module: ModuleNode,
  File: FileNode,
  Api: ApiNode,
  Database: DatabaseNode,
};

const EDGE_COLORS: Record<string, string> = {
  IMPORTS: "#6366f1",
  DEPENDS_ON: "#f59e0b",
  CALLS: "#10b981",
  CONTAINS: "#6b7280",
  DEFINES: "#ec4899",
  READS: "#3b82f6",
  WRITES: "#ef4444",
};

function toFlowNodes(graphNodes: GraphNode[]): Node[] {
  return graphNodes.map((n, i) => ({
    id: n.id,
    type: n.type,
    position: { x: (i % 10) * 220, y: Math.floor(i / 10) * 160 },
    data: { label: n.label, properties: n.properties },
  }));
}

function toFlowEdges(graphEdges: GraphEdge[]): Edge[] {
  return graphEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.type,
    animated: e.type === "CALLS",
    style: { stroke: EDGE_COLORS[e.type] ?? "#6b7280", strokeWidth: 1.5 },
    labelStyle: { fill: "#9ca3af", fontSize: 10 },
    labelBgStyle: { fill: "#1a1a2e" },
  }));
}

interface ArchitectureGraphProps {
  repoId: string;
}

export function ArchitectureGraph({ repoId }: ArchitectureGraphProps) {
  const { data, loading, error } = useGraph(repoId);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const { detail, loading: detailLoading } = useNodeDetail(repoId, selectedNodeId);

  const initialNodes = useMemo(() => data ? toFlowNodes(data.nodes) : [], [data]);
  const initialEdges = useMemo(() => data ? toFlowEdges(data.edges) : [], [data]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes when data changes
  useMemo(() => {
    if (data) {
      const newNodes = toFlowNodes(data.nodes).map(n => ({
        ...n,
        style: search && !n.data.label.toString().toLowerCase().includes(search.toLowerCase())
          ? { opacity: 0.2 }
          : undefined,
      }));
      setNodes(newNodes);
    }
  }, [data, search, setNodes]);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id === selectedNodeId ? null : node.id);
  }, [selectedNodeId]);

  if (loading) return (
    <div className="w-full h-full flex items-center justify-center text-muted-foreground text-sm">
      <div className="text-center space-y-2">
        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
        <p>Loading architecture graph…</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="w-full h-full flex items-center justify-center text-muted-foreground text-sm text-center p-8">
      <p>{error}</p>
    </div>
  );

  if (!data || data.nodes.length === 0) return (
    <div className="w-full h-full flex items-center justify-center text-muted-foreground text-sm text-center p-8">
      <p>No graph data yet. Scan the repository first.</p>
    </div>
  );

  return (
    <div className="w-full h-full relative">
      {/* Search bar */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-card border rounded-lg px-3 py-2 shadow-lg w-64">
        <Search className="w-4 h-4 text-muted-foreground shrink-0" />
        <input
          type="text"
          placeholder="Search nodes…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="bg-transparent text-sm outline-none placeholder:text-muted-foreground flex-1"
        />
      </div>

      {/* Stats */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-4 bg-card border rounded-lg px-4 py-2 shadow-lg text-xs text-muted-foreground">
        <span>{data.node_count} nodes</span>
        <span className="w-px h-3 bg-border" />
        <span>{data.edge_count} edges</span>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-card border rounded-lg p-3 shadow-lg">
        <p className="text-xs text-muted-foreground font-medium mb-2">Edge types</p>
        <div className="space-y-1">
          {Object.entries(EDGE_COLORS).slice(0, 5).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2">
              <div className="w-4 h-0.5 rounded" style={{ backgroundColor: color }} />
              <span className="text-xs text-muted-foreground">{type}</span>
            </div>
          ))}
        </div>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        colorMode="dark"
      >
        <Background variant={BackgroundVariant.Dots} color="#374151" gap={20} />
        <Controls />
        <MiniMap
          nodeColor={(n) => {
            const colors: Record<string, string> = { Service: "#1e40af", Module: "#6d28d9", File: "#374151", Api: "#92400e", Database: "#991b1b" };
            return colors[n.type ?? ""] ?? "#374151";
          }}
          style={{ background: "#111827", border: "1px solid #374151" }}
        />
      </ReactFlow>

      {/* Node detail panel */}
      <NodeDetailPanel
        detail={detail}
        loading={detailLoading}
        onClose={() => setSelectedNodeId(null)}
        onNodeSelect={setSelectedNodeId}
      />
    </div>
  );
}
