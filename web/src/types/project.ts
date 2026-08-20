export interface Workspace {
  id: number;
  name: string;
  owner_id: number;
  created_at: string;
}

export interface Project {
  id: number;
  workspace_id: number;
  project_name: string;
  project_path: string;
  created_at: string;
}

export interface Decision {
  title: string;
  strategy: string;
  confidence: number;
  reason: string;
}

export interface Recommendation {
  priority: number;
  title: string;
  description: string;
}

export interface DatasetSummary {
  path: string;
  rows: number;
  columns: number;
}

export interface ProjectDetails {
  id: number;
  project_name: string;
  project_path: string;
  status: 'active' | 'no_project';
  dataset: {
    path: string | null;
    target: string | null;
    problem_type: string | null;
    rows: number;
    columns: number;
  } | null;
  profile: {
    problem_type: string;
    complexity: 'low' | 'medium' | 'high' | string;
    baseline_models: string[];
    risks: string[];
  } | null;
  metrics: Record<string, number>;
  decisions: Decision[];
  recommendations: Recommendation[];
}

export interface AnalysisReport {
  dataset_summary: DatasetSummary;
  decisions: Decision[];
  recommendations: Recommendation[];
}

export interface ExperimentTrial {
  trial_id: string;
  model_name: string;
  estimator_class: string;
  metric: string;
  score: number;
  cv_mean: number;
  cv_std: number;
  cv_scores: number[];
  parameters: Record<string, any>;
  rank: number;
  status: 'SUCCESS' | 'FAILED' | string;
  selected: boolean;
  duration_seconds: number;
  error?: string | null;
}

export interface Experiment {
  experiment_id: string;
  timestamp?: string;
  dataset_fingerprint?: string;
  problem_type?: string;
  selected_model?: string;
  candidate_models?: string[];
  metrics?: Record<string, number | string>;
  cv_scores?: number[];
  training_time_s?: number;
  prediction_time_s?: number;
  memory_usage_mb?: number;
  feature_importance?: Record<string, number>;
  artifacts?: Record<string, string>;
  hyperparameters?: Record<string, any>;
  status?: 'SUCCESS' | 'FAILED' | string;
  pipeline_id?: string;
  candidate_trials?: ExperimentTrial[];
}
