import { create } from 'zustand';
import { api } from '../api/client';

export const useTranscribeStore = create((set, get) => ({
  tasks: {}, // { taskId: taskData }
  currentTaskId: null,
  
  uploadFile: async (formData) => {
    const res = await api.transcriptions.upload(formData);
    const taskId = res.data.task_id;
    set((state) => ({
      currentTaskId: taskId,
      tasks: {
        ...state.tasks,
        [taskId]: { id: taskId, status: 'queued', progress: 0 }
      }
    }));
    return taskId;
  },
  
  updateTaskStatus: async (taskId) => {
    try {
      const res = await api.transcriptions.status(taskId);
      set((state) => ({
        tasks: {
          ...state.tasks,
          [taskId]: res.data
        }
      }));
      return res.data;
    } catch (err) {
      console.error('Failed to poll status', err);
      throw err;
    }
  },

  setCurrentTaskId: (taskId) => set({ currentTaskId: taskId }),
  
  clearCurrentTask: () => set({ currentTaskId: null }),
}));
