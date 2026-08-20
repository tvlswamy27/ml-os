import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectService } from '../services/projectService';
import type { Project, ProjectDetails, Experiment } from '../types';

export function useProjects(workspaceId: number | null) {
  const queryClient = useQueryClient();

  const projectsQuery = useQuery<Project[], Error>({
    queryKey: ['projects', workspaceId],
    queryFn: () => projectService.listProjects(workspaceId!),
    enabled: workspaceId !== null && !isNaN(workspaceId),
    staleTime: 30000,
  });

  const createProjectMutation = useMutation({
    mutationFn: ({ projectName, projectPath }: { projectName: string; projectPath: string }) =>
      projectService.createProject(workspaceId!, projectName, projectPath),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', workspaceId] });
    },
  });

  return {
    projects: projectsQuery.data || [],
    isLoading: projectsQuery.isLoading,
    isError: projectsQuery.isError,
    error: projectsQuery.error,
    projectsQuery,
    createProjectMutation,
  };
}

export function useProject(projectId: number | null) {
  const projectQuery = useQuery<Project, Error>({
    queryKey: ['project', projectId],
    queryFn: () => projectService.getProject(projectId!),
    enabled: projectId !== null && !isNaN(projectId),
    staleTime: 30000,
  });

  return {
    project: projectQuery.data || null,
    isLoading: projectQuery.isLoading,
    isError: projectQuery.isError,
    error: projectQuery.error,
    projectQuery,
  };
}

export function useProjectDetails(projectId: number | null) {
  const detailsQuery = useQuery<ProjectDetails, Error>({
    queryKey: ['projectDetails', projectId],
    queryFn: () => projectService.getProjectDetails(projectId!),
    enabled: projectId !== null && !isNaN(projectId),
    staleTime: 30000,
  });

  return {
    details: detailsQuery.data || null,
    isLoading: detailsQuery.isLoading,
    isError: detailsQuery.isError,
    error: detailsQuery.error,
    detailsQuery,
  };
}

export function useProjectExperiments(projectId: number | null) {
  const experimentsQuery = useQuery<Experiment[], Error>({
    queryKey: ['projectExperiments', projectId],
    queryFn: () => projectService.getExperiments(projectId!),
    enabled: projectId !== null && !isNaN(projectId),
    staleTime: 30000,
  });

  return {
    experiments: experimentsQuery.data || [],
    isLoading: experimentsQuery.isLoading,
    isError: experimentsQuery.isError,
    error: experimentsQuery.error,
    experimentsQuery,
  };
}
