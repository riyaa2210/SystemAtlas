/**
 * Zustand store for repository state.
 */
import { create } from "zustand";
import type { Repository } from "@/types/repository";

interface RepoState {
  repositories: Repository[];
  selectedRepo: Repository | null;
  setRepositories: (repos: Repository[]) => void;
  addRepository: (repo: Repository) => void;
  removeRepository: (id: string) => void;
  selectRepository: (repo: Repository | null) => void;
}

export const useRepoStore = create<RepoState>((set) => ({
  repositories: [],
  selectedRepo: null,

  setRepositories: (repositories) => set({ repositories }),

  addRepository: (repo) =>
    set((state) => ({ repositories: [repo, ...state.repositories] })),

  removeRepository: (id) =>
    set((state) => ({
      repositories: state.repositories.filter((r) => r.id !== id),
    })),

  selectRepository: (selectedRepo) => set({ selectedRepo }),
}));
