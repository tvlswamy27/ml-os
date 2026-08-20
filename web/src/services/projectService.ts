import { apiClient } from './apiClient';
import type { Workspace, Project, ProjectDetails, AnalysisReport, Experiment } from '../types';

export const projectService = {
  listWorkspaces: async (): Promise<Workspace[]> => {
    return apiClient.get<Workspace[]>('/api/workspaces');
  },

  createWorkspace: async (name: string): Promise<Workspace> => {
    return apiClient.post<Workspace>('/api/workspaces', { name });
  },

  listProjects: async (workspaceId: number): Promise<Project[]> => {
    return apiClient.get<Project[]>(`/api/projects?workspace_id=${workspaceId}`);
  },

  createProject: async (workspaceId: number, projectName: string, projectPath: string): Promise<Project> => {
    return apiClient.post<Project>(`/api/projects?workspace_id=${workspaceId}`, {
      project_name: projectName,
      project_path: projectPath,
    });
  },

  getProject: async (projectId: number): Promise<Project> => {
    return apiClient.get<Project>(`/api/projects/${projectId}`);
  },

  getProjectDetails: async (projectId: number): Promise<ProjectDetails> => {
    return apiClient.get<ProjectDetails>(`/api/projects/${projectId}/details`);
  },

  analyzeProject: async (projectId: number, datasetPath: string, targetColumn?: string): Promise<AnalysisReport> => {
    return apiClient.post<AnalysisReport>(`/api/projects/${projectId}/analyze`, {
      dataset_path: datasetPath,
      target_column: targetColumn,
    });
  },

  getExperiments: async (projectId: number): Promise<Experiment[]> => {
    return apiClient.get<Experiment[]>(`/api/projects/${projectId}/experiments`);
  },
};
