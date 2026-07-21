"use client";
import { X, ArrowRight, ArrowLeft } from "lucide-react";
import type { NodeDetail } from "@/types/graph";

interface NodeDetailPanelProps {
  detail: NodeDetail | null;
  loading: boolean;
  onClose: () => void;
  onNodeSelect: (id: string) => void;
}

export function NodeDetailPanel({ detail, loading, onClose, onNodeSelect }: NodeDetailPanelProps) {
  if (!detail && !loading) return null;
  return (
    <div className="absolute right-4 top-4 bottom-4 w-72 bg-card border rounded-xl shadow-2xl flex flex-col overflow-hidden z-10">
      <div className="flex items-center justify-between px-4 py-3 border-b shrink-0">
        <h3 className="font-semibold text-sm truncate">{detail?.node.label ?? "Loading…"}</h3>
        <button onClick={onClose} className="p-1 rounded hover:bg-secondary transition-colors shrink-0"><X className="w-4 h-4" /></button>
      </div>
      {loading && <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground">Loading…</div>}
      {detail && !loading && (
        <div className="flex-1 overflow-y-auto p-4 space-y-4 text-sm">
          <div>
            <span className="text-xs text-muted-foreground uppercase tracking-wide">Type</span>
            <p className="font-medium mt-0.5">{detail.node.type}</p>
          </div>
          {detail.node.properties.path && (
            <div>
              <span className="text-xs text-muted-foreground uppercase tracking-wide">Path</span>
              <p className="font-mono text-xs mt-0.5 break-all text-muted-foreground">{String(detail.node.properties.path)}</p>
            </div>
          )}
          {detail.node.properties.language && (
            <div>
              <span className="text-xs text-muted-foreground uppercase tracking-wide">Language</span>
              <p className="font-medium mt-0.5">{String(detail.node.properties.language)}</p>
            </div>
          )}
          {detail.outgoing_edges.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1"><ArrowRight className="w-3 h-3" /> Outgoing ({detail.outgoing_edges.length})</span>
              <div className="mt-1 space-y-1">
                {detail.outgoing_edges.slice(0, 8).map((e, i) => (
                  <button key={i} onClick={() => onNodeSelect((e as {node: {id: string}}).node.id)} className="w-full text-left text-xs px-2 py-1 rounded hover:bg-secondary transition-colors flex items-center justify-between gap-2">
                    <span className="truncate">{(e as {node: {label: string}}).node.label}</span>
                    <span className="text-muted-foreground shrink-0">{(e as {type: string}).type}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
          {detail.incoming_edges.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1"><ArrowLeft className="w-3 h-3" /> Incoming ({detail.incoming_edges.length})</span>
              <div className="mt-1 space-y-1">
                {detail.incoming_edges.slice(0, 8).map((e, i) => (
                  <button key={i} onClick={() => onNodeSelect((e as {node: {id: string}}).node.id)} className="w-full text-left text-xs px-2 py-1 rounded hover:bg-secondary transition-colors flex items-center justify-between gap-2">
                    <span className="truncate">{(e as {node: {label: string}}).node.label}</span>
                    <span className="text-muted-foreground shrink-0">{(e as {type: string}).type}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
