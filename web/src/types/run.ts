export interface RunStatusResponse {
  run_id: string;
  status: 'queued' | 'running' | 'cancel_requested' | 'cancelled' | 'completed' | 'failed';
  current_stage: string | null;
  completed_stages: string[];
  failed_stage?: string | null;
  started_at: string;
  completed_at: string | null;
  experiment_id?: string;
  problem_type?: string;
  execution_time_s?: number;
  artifacts_count?: number;
  metrics?: Record<string, any>;
  error?: string | null;
}
