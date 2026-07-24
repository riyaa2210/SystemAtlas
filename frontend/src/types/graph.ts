export type NodeType = "Service" | "Module" | "File" | "Api" | "Database";
export type EdgeType = "CALLS" | "IMPORTS" | "DEPENDS_ON" | "READS" | "WRITES" | "CONTAINS";

export interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  properties: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  repo_id: string;
  node_count: number;
  edge_count: number;
}

export interface NodeDetail {
  node: GraphNode;
  neighbors: GraphNode[];
  incoming_edges: GraphEdge[];
  outgoing_edges: GraphEdge[];
}
