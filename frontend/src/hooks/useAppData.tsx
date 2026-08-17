import * as React from "react";
import { api } from "@/services/api";
import type { Repository } from "@/types";

interface AppDataContextValue {
  repositories: Repository[];
  selectedRepoId: string | null;
  selectedRepo: Repository | null;
  setSelectedRepoId: (id: string) => void;
  refreshRepositories: () => Promise<void>;
  loading: boolean;
  health: { github_configured: boolean; anthropic_configured: boolean } | null;
}

const AppDataContext = React.createContext<AppDataContextValue | null>(null);

export function AppDataProvider({ children }: { children: React.ReactNode }) {
  const [repositories, setRepositories] = React.useState<Repository[]>([]);
  const [selectedRepoId, setSelectedRepoIdState] = React.useState<string | null>(
    () => localStorage.getItem("sentinelchain.selectedRepoId")
  );
  const [loading, setLoading] = React.useState(true);
  const [health, setHealth] = React.useState<AppDataContextValue["health"]>(null);

  const refreshRepositories = React.useCallback(async () => {
    try {
      await api.ensureDemoRepository();
      const repos = await api.listRepositories();
      setRepositories(repos);
      setSelectedRepoIdState((current) => {
        if (current && repos.some((r) => r.id === current)) return current;
        return repos[0]?.id ?? null;
      });
    } catch (e) {
      console.error("Failed to load repositories", e);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    refreshRepositories();
    api.health().then(setHealth).catch(() => setHealth({ github_configured: false, anthropic_configured: false }));
  }, [refreshRepositories]);

  const setSelectedRepoId = (id: string) => {
    setSelectedRepoIdState(id);
    localStorage.setItem("sentinelchain.selectedRepoId", id);
  };

  const selectedRepo = repositories.find((r) => r.id === selectedRepoId) ?? null;

  return (
    <AppDataContext.Provider
      value={{ repositories, selectedRepoId, selectedRepo, setSelectedRepoId, refreshRepositories, loading, health }}
    >
      {children}
    </AppDataContext.Provider>
  );
}

export function useAppData() {
  const ctx = React.useContext(AppDataContext);
  if (!ctx) throw new Error("useAppData must be used within AppDataProvider");
  return ctx;
}
