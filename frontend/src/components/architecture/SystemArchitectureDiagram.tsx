"use client";

import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  BackgroundVariant,
  type Node,
  type Edge,
  type NodeTypes,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { ArchLayerNode, type ArchLayerNodeData } from "./ArchLayerNode";
import { useArchitecture } from "@/hooks/useArchitecture";
import type { ArchitectureNode, ArchitectureEdge } from "@/types/architecture";
import { RefreshCw, Layers, Code2, Cpu } from "lucide-react";

const nodeTypes: NodeTypes = {
  archLayer: ArchLayerNode,
};

// ── Converters ───────────────────────────────────────────────────────────────

function toFlowNodes(archNodes: ArchitectureNode[]): Node[] {
  // Layout: single centered column, spaced 180px apart vertically
  return archNodes.map((n, i) => ({
    id: n.id,
    type: "archLayer",
    position: { x: n.position.x, y: i * 180 },
    data: {
      label: n.label,
      layer: n.layer,
      technologies: n.technologies,
      file_count: n.file_count,
      color: n.color,
      icon: n.icon,
      description: n.description,
    } satisfies ArchLayerNodeData,
    draggable: true,
  }));
}

function toFlowEdges(archEdges: ArchitectureEdge[]): Edge[] {
  return archEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.label || undefined,
    animated: false,
    type: "smoothstep",
    markerEnd: { type: MarkerType.ArrowClosed, color: "#6366f1", width: 16, height: 16 },
    style: { stroke: "#6366f1", strokeWidth: 2, opacity: 0.7 },
    labelStyle: { fill: "#9ca3af", fontSize: 10 },
    labelBgStyle: { fill: "#1e1e2e", fillOpacity: 0.9 },
    labelBgPadding: [4, 2] as [number, number],
    labelBgBorderRadius: 4,
  }));
}

// ── Component ────────────────────────────────────────────────────────────────

interface SystemArchitectureDiagramProps {
  repoId: string;
}

export function SystemArchitectureDiagram({ repoId }: SystemArchitectureDiagramProps) {
  const { data, loading, error, refresh } = useArchitecture(repoId);

  const nodes = useMemo(() => (data ? toFlowNodes(data.nodes) : []), [data]);
  const edges = useMemo(() => (data ? toFlowEdges(data.edges) : []), [data]);

  // ── States ────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center text-muted-foreground text-sm">
        <div className="text-center space-y-2">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p>Loading architecture diagram…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center text-sm text-center p-8">
        <div className="space-y-3">
          <p className="text-muted-foreground">{error}</p>
          <button onClick={refresh} className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg border border-border/60 hover:bg-secondary/80 transition-colors">
            <RefreshCw className="w-3.5 h-3.5" /> Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data || data.nodes.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center text-sm text-center p-8">
        <div className="space-y-3 max-w-sm">
          <div className="w-12 h-12 rounded-2xl bg-secondary/60 flex items-center justify-center mx-auto">
            <Layers className="w-6 h-6 text-muted-foreground" />
          </div>
          <p className="font-medium">No architecture data yet</p>
          <p className="text-muted-foreground text-xs leading-relaxed">
            Rescan this repository to generate the system architecture diagram.
            The diagram is automatically inferred from folder structure, imports, and frameworks.
          </p>
        </div>
      </div>
    );
  }

  const { metadata } = data;

  return (
    <div className="w-full h-full relative">
      {/* Header stats overlay */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-4 bg-card/90 backdrop-blur-sm border border-border/60 rounded-xl px-4 py-2 shadow-lg text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-primary" />
          {data.node_count} layer{data.node_count !== 1 ? "s" : ""}
        </span>
        <span className="w-px h-3 bg-border" />
        <span className="flex items-center gap-1.5">
          <Cpu className="w-3.5 h-3.5 text-emerald-400" />
          {metadata.detected_technologies.length} technolog{metadata.detected_technologies.length !== 1 ? "ies" : "y"}
        </span>
        {metadata.frameworks.length > 0 && (
          <>
            <span className="w-px h-3 bg-border" />
            <span className="flex items-center gap-1.5">
              <Code2 className="w-3.5 h-3.5 text-violet-400" />
              {metadata.frameworks.slice(0, 3).join(", ")}
              {metadata.frameworks.length > 3 && ` +${metadata.frameworks.length - 3}`}
            </span>
          </>
        )}
      </div>

      {/* Technology legend */}
      {metadata.detected_technologies.length > 0 && (
        <div className="absolute bottom-4 right-4 z-10 bg-card/90 backdrop-blur-sm border border-border/60 rounded-xl p-3 shadow-lg max-w-[200px]">
          <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider mb-2">
            Detected Technologies
          </p>
          <div className="flex flex-wrap gap-1">
            {metadata.detected_technologies.slice(0, 12).map((tech) => (
              <span key={tech} className="text-[10px] px-1.5 py-0.5 rounded bg-secondary/60 text-muted-foreground border border-border/40">
                {tech}
              </span>
            ))}
            {metadata.detected_technologies.length > 12 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-secondary/60 text-muted-foreground border border-border/40">
                +{metadata.detected_technologies.length - 12} more
              </span>
            )}
          </div>
        </div>
      )}

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        minZoom={0.2}
        maxZoom={2}
        colorMode="dark"
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} color="#1e293b" gap={24} size={1.5} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
