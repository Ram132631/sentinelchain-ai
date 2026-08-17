import * as React from "react";
import { ScrollText, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import { useAppData } from "@/hooks/useAppData";
import { api } from "@/services/api";
import type { AuditLogEntry } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";

const SEVERITY_ICON: Record<string, any> = {
  INFO: CheckCircle2,
  WARNING: AlertTriangle,
  ERROR: XCircle,
};

export function AuditLogsPage() {
  const { selectedRepoId } = useAppData();
  const [logs, setLogs] = React.useState<AuditLogEntry[] | null>(null);

  React.useEffect(() => {
    if (!selectedRepoId) return;
    setLogs(null);
    api.listAuditLogs(selectedRepoId, 300).then(setLogs);
    const interval = setInterval(() => api.listAuditLogs(selectedRepoId, 300).then(setLogs), 5000);
    return () => clearInterval(interval);
  }, [selectedRepoId]);

  return (
    <div>
      <PageHeader title="Audit Logs" description="Every autonomous action, timestamped and attributable." />

      {!logs ? (
        <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
      ) : logs.length === 0 ? (
        <EmptyState icon={ScrollText} title="No audit entries yet" description="Run a scan to begin generating an audit trail." />
      ) : (
        <Card className="divide-y divide-border">
          {logs.map((log) => {
            const Icon = SEVERITY_ICON[log.severity] || CheckCircle2;
            return (
              <div key={log.id} className="flex items-start gap-3 p-3">
                <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${log.severity === "ERROR" ? "text-critical" : log.severity === "WARNING" ? "text-medium" : "text-safe"}`} />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="mono-tabular text-xs text-muted-foreground">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <Badge variant="outline">{log.agent_name}</Badge>
                    {log.user_approval !== null && (
                      <Badge variant={log.user_approval ? "success" : "critical"}>
                        {log.user_approval ? "Approved" : "Rejected"}
                      </Badge>
                    )}
                  </div>
                  <p className="mt-1 text-sm">{log.action}</p>
                  {log.output_data && <p className="mt-0.5 truncate text-xs text-muted-foreground">{log.output_data}</p>}
                </div>
              </div>
            );
          })}
        </Card>
      )}
    </div>
  );
}
