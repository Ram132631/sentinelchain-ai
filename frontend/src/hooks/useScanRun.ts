import * as React from "react";
import { api } from "@/services/api";
import type { ScanRun } from "@/types";

const ACTIVE_STATES = new Set(["RUNNING", "WAITING_FOR_APPROVAL"]);

export function useScanRun(repositoryId: string | null) {
  const [scanRun, setScanRun] = React.useState<ScanRun | null>(null);
  const [loading, setLoading] = React.useState(true);

  const refresh = React.useCallback(async () => {
    if (!repositoryId) {
      setScanRun(null);
      setLoading(false);
      return;
    }
    try {
      const run = await api.latestScanRun(repositoryId);
      setScanRun(run);
    } catch {
      setScanRun(null);
    } finally {
      setLoading(false);
    }
  }, [repositoryId]);

  React.useEffect(() => {
    setLoading(true);
    refresh();
  }, [refresh]);

  React.useEffect(() => {
    if (!scanRun || !ACTIVE_STATES.has(scanRun.status)) return;
    const interval = setInterval(refresh, 1200);
    return () => clearInterval(interval);
  }, [scanRun, refresh]);

  const startScan = React.useCallback(async () => {
    if (!repositoryId) return;
    const run = await api.triggerScan(repositoryId);
    setScanRun(run);
    return run;
  }, [repositoryId]);

  return { scanRun, loading, refresh, startScan, isActive: !!scanRun && ACTIVE_STATES.has(scanRun.status) };
}
