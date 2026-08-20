import { create } from 'zustand';

interface UIState {
  selectedWorkspaceId: number | null;
  selectedProjectId: number | null;
  activeRunId: string | null;
  learnMode: boolean;
  setSelectedWorkspaceId: (id: number | null) => void;
  setSelectedProjectId: (id: number | null) => void;
  setActiveRunId: (id: string | null) => void;
  toggleLearnMode: () => void;
}

const getStoredNumber = (key: string): number | null => {
  const val = localStorage.getItem(key);
  if (val === null) return null;
  const parsed = parseInt(val, 10);
  return isNaN(parsed) ? null : parsed;
};

export const useProjectStore = create<UIState>((set) => ({
  selectedWorkspaceId: getStoredNumber('mlos_selected_workspace_id'),
  selectedProjectId: getStoredNumber('mlos_selected_project_id'),
  activeRunId: localStorage.getItem('mlos_active_run_id'),
  learnMode: localStorage.getItem('mlos_learn_mode') === 'true',
  setSelectedWorkspaceId: (id) =>
    set(() => {
      if (id === null) {
        localStorage.removeItem('mlos_selected_workspace_id');
      } else {
        localStorage.setItem('mlos_selected_workspace_id', String(id));
      }
      return { selectedWorkspaceId: id };
    }),
  setSelectedProjectId: (id) =>
    set(() => {
      if (id === null) {
        localStorage.removeItem('mlos_selected_project_id');
      } else {
        localStorage.setItem('mlos_selected_project_id', String(id));
      }
      return { selectedProjectId: id };
    }),
  setActiveRunId: (id) =>
    set(() => {
      if (id === null) {
        localStorage.removeItem('mlos_active_run_id');
      } else {
        localStorage.setItem('mlos_active_run_id', id);
      }
      return { activeRunId: id };
    }),
  toggleLearnMode: () =>
    set((state) => {
      const newMode = !state.learnMode;
      localStorage.setItem('mlos_learn_mode', String(newMode));
      return { learnMode: newMode };
    }),
}));
