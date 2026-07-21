export interface Repository {
  id: string;
  name: string;
  full_name: string;
  github_url: string;
  description: string | null;
  languages: string[];
  frameworks: string[];
  default_branch: string;
  is_private: boolean;
  star_count: number;
  created_at: string;
  updated_at: string;
  latest_scan?: ScanJob | null;
}

export interface ScanJob {
  id: string;
  repository_id: string;
  status: "pending" | "running" | "completed" | "failed";
  stage: string | null;
  error_message: string | null;
  files_scanned: number;
  nodes_created: number;
  edges_created: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}
