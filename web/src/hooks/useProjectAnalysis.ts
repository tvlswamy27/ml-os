import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectService } from '../services/projectService';
import type { AnalysisReport } from '../types';

export function useAnalyzeProject(projectId: number | null) {
  const queryClient = useQueryClient();

  const analyzeMutation = useMutation<AnalysisReport, Error, { datasetPath: string; targetColumn?: string }>({
    mutationFn: ({ datasetPath, targetColumn }) =>
      projectService.analyzeProject(projectId!, datasetPath, targetColumn),
    onSuccess: (data) => {
      // Store analysis report in query cache under the project's analysis key
      queryClient.setQueryData(['projectAnalysis', projectId], data);
      queryClient.invalidateQueries({ queryKey: ['projectDetails', projectId] });
    },
  });

  return {
    analyzeMutation,
    analysisReport: queryClient.getQueryData<AnalysisReport>(['projectAnalysis', projectId]) || null,
  };
}
