export interface AnalyticsData {
  id: string;
  repository_id: string;
  architecture_score: number;
  total_modules: number;
  total_files: number;
  total_dependencies: number;
  circular_deps: number;
  dead_modules: number;
  highly_coupled: number;
  missing_docs: number;
  metrics_json: Record<string, unknown> | null;
  created_at: string;
}

export type RiskSeverity = "high" | "medium" | "low";
export type RiskType =
  | "circular_dependency"
  | "high_coupling"
  | "dead_module"
  | "missing_docs";

export interface RiskItem {
  type: RiskType;
  severity: RiskSeverity;
  title: string;
  description: string;
  affected_nodes: string[];
}
