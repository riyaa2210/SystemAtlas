export interface ArchNodePosition {
  x: number;
  y: number;
}

export interface ArchitectureNode {
  id: string;
  layer: string;
  label: string;
  technologies: string[];
  file_count: number;
  color: string;
  icon: string;
  description: string;
  position: ArchNodePosition;
}

export interface ArchitectureEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  type: string;
}

export interface ArchitectureMetadata {
  detected_technologies: string[];
  detected_layers: string[];
  frameworks: string[];
  languages: string[];
}

export interface ArchitectureData {
  nodes: ArchitectureNode[];
  edges: ArchitectureEdge[];
  metadata: ArchitectureMetadata;
  repo_id: string;
  node_count: number;
  edge_count: number;
}
