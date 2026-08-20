import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { runService } from '../services/runService';
import type { RunStatusResponse } from '../types';

export function useRun(projectId: number | null, runId: string | null) {
  const queryClient = useQueryClient();

  const runStatusQuery = useQuery<RunStatusResponse, Error>({
    queryKey: ['runStatus', projectId, runId],
    queryFn: () => runService.getRunStatus(projectId!, runId!),
    enabled: projectId !== null && !isNaN(projectId) && runId !== null && runId !== '',
    refetchInterval: (query) => {
      // If status is terminal, stop polling.
      const status = query.state.data?.status;
      if (status && ['completed', 'failed', 'cancelled'].includes(status)) {
        return false;
      }
      return 3000; // Poll every 3 seconds as a fallback if SSE drops
    },
  });

  const startRunMutation = useMutation({
    mutationFn: ({ datasetPath, targetColumn }: { datasetPath: string; targetColumn?: string }) =>
      runService.startRun(projectId!, datasetPath, targetColumn),
  });

  const cancelRunMutation = useMutation({
    mutationFn: () => runService.cancelRun(projectId!, runId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runStatus', projectId, runId] });
    },
  });

  return {
    runStatus: runStatusQuery.data || null,
    isLoading: runStatusQuery.isLoading,
    isError: runStatusQuery.isError,
    error: runStatusQuery.error,
    runStatusQuery,
    startRunMutation,
    cancelRunMutation,
  };
}
