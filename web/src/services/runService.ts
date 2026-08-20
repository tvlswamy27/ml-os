import { apiClient } from './apiClient';

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

export const runService = {
  startRun: async (projectId: number, datasetPath: string, targetColumn?: string): Promise<{ run_id: string; message: string }> => {
    return apiClient.post<{ run_id: string; message: string }>(`/api/projects/${projectId}/run`, {
      dataset_path: datasetPath,
      target_column: targetColumn,
    });
  },

  cancelRun: async (projectId: number, runId: string): Promise<{ message: string; run_id: string }> => {
    return apiClient.post<{ message: string; run_id: string }>(`/api/projects/${projectId}/run/cancel/${runId}`);
  },

  getRunStatus: async (projectId: number, runId: string): Promise<RunStatusResponse> => {
    return apiClient.get<RunStatusResponse>(`/api/projects/${projectId}/run/status/${runId}`);
  },
};
