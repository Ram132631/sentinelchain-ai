import * as React from "react";
import { useNavigate } from "react-router-dom";
import {
  CheckCircle2, Loader2, Circle, XCircle, UserCheck, Play, ChevronDown, ChevronUp,
} from "lucide-react";
import { useAppData } from "@/hooks/useAppData";
import { useScanRun } from "@/hooks/useScanRun";
import { api } from "@/services/api";
import type { AgentExecution, Approval } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/EmptyState";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";
import { Bot } from "lucide-react";

const STATUS_META: Record<string, { icon: any; color: string; label: string }> = {
  PENDING: { icon: Circle, color: "text-muted-foreground", label: "PENDING" },
  RUNNING: { icon: Loader2, color: "text-primary", label: "RUNNING" },
  COMPLETED: { icon: CheckCircle2, color: "text-safe", label: "COMPLETED" },
  FAILED: { icon: XCircle, color: "text-critical", label: "FAILED" },
  WAITING_FOR_APPROVAL: { icon: UserCheck, color: "text-medium", label: "WAITING FOR APPROVAL" },
  REJECTED: { icon: XCircle, color: "text-critical", label: "REJECTED" },
};

function AgentNode({ ex }: { ex: AgentExecution }) {
  const [expanded, setExpanded] = React.useState(false);
  const meta = STATUS_META[ex.status] || STATUS_META.PENDING;
  const Icon = meta.icon;

  return (
    <Card className={cn("transition-all", ex.status === "RUNNING" && "ring-1 ring-primary/50 animate-pulse-ring")}>
      <button className="flex w-full items-center gap-3 p-4 text-left" onClick={() => setExpanded((e) => !e)}>
        <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border bg-muted", meta.color)}>
          <Icon className={cn("h-4 w-4", ex.status === "RUNNING" && "animate-spin")} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold">{ex.agent_name}</p>
            <Badge variant={ex.status === "COMPLETED" ? "success" : ex.status === "RUNNING" ? "info" : ex.status === "WAITING_FOR_APPROVAL" ? "medium" : ex.status === "PENDING" ? "muted" : "critical"}>
              {meta.label}
            </Badge>
          </div>
          <p className="truncate text-xs text-muted-foreground">{ex.current_task || ex.output_summary || "Waiting to start…"}</p>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {ex.duration_ms > 0 && <span className="mono-tabular">{(ex.duration_ms / 1000).toFixed(1)}s</span>}
          {ex.confidence > 0 && <span className="mono-tabular hidden sm:inline">{ex.confidence}% confidence</span>}
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>
      {expanded && (
        <CardContent className="border-t border-border pt-3 text-xs">
          {ex.output_summary && (
            <div className="mb-2">
              <p className="mb-1 font-semibold text-muted-foreground">Output</p>
              <p className="text-foreground/90">{ex.output_summary}</p>
            </div>
          )}
          {ex.reasoning && (
            <div className="mb-2">
              <p className="mb-1 font-semibold text-muted-foreground">Reasoning</p>
              <p className="text-foreground/90">{ex.reasoning}</p>
            </div>
          )}
          {ex.tools_used?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {ex.tools_used.map((t) => <Badge key={t} variant="outline">{t}</Badge>)}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}

export function AgentMonitorPage() {
  const { selectedRepoId, selectedRepo } = useAppData();
  const { scanRun, isActive, startScan } = useScanRun(selectedRepoId);
  const [approvals, setApprovals] = React.useState<Approval[]>([]);
  const { toast } = useToast();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (scanRun?.status === "WAITING_FOR_APPROVAL") {
      api.listApprovals({ repositoryId: selectedRepoId!, decision: "PENDING" }).then(setApprovals);
    } else {
      setApprovals([]);
    }
  }, [scanRun?.status, selectedRepoId]);

  const handleScan = async () => {
    await startScan();
    toast({ title: "Autonomous security scan started" });
  };

  const decide = async (id: string, decision: "APPROVED" | "REJECTED") => {
    await api.decideApproval(id, decision, decision === "APPROVED" ? "Verified fix and QA results." : "Needs further review.");
    setApprovals((prev) => prev.filter((a) => a.id !== id));
    toast({ title: `Change ${decision.toLowerCase()}`, variant: decision === "APPROVED" ? "success" : "warning" });
  };

  return (
    <div>
      <PageHeader
        title="AI Agent Orchestration"
        description={selectedRepo ? `Live pipeline for ${selectedRepo.name}` : "Select a repository"}
        actions={
          <Button onClick={handleScan} disabled={!selectedRepoId || isActive}>
            {isActive ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {isActive ? "Scan Running…" : "Run Autonomous Security Scan"}
          </Button>
        }
      />

      {!scanRun ? (
        <EmptyState icon={Bot} title="No scan has run yet" description="Click 'Run Autonomous Security Scan' to watch all 13 agents work in sequence." />
      ) : (
        <>
          {scanRun.status === "WAITING_FOR_APPROVAL" && approvals.length > 0 && (
            <Card className="mb-4 border-medium/40 bg-medium/5">
              <CardContent className="pt-5">
                <div className="mb-3 flex items-center gap-2">
                  <UserCheck className="h-4 w-4 text-medium" />
                  <p className="text-sm font-semibold">Human Approval Required</p>
                </div>
                <div className="space-y-3">
                  {approvals.map((a) => (
                    <div key={a.id} className="rounded-md border border-border bg-card/60 p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <p className="text-sm font-medium">{a.proposed_change}</p>
                          <p className="mt-1 text-xs text-muted-foreground">{a.ai_reasoning}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={a.risk_level.toLowerCase() as any}>{a.risk_level}</Badge>
                          <Button size="sm" variant="success" onClick={() => decide(a.id, "APPROVED")}>Approve</Button>
                          <Button size="sm" variant="destructive" onClick={() => decide(a.id, "REJECTED")}>Reject</Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {scanRun.status === "COMPLETED" && (
            <Card className="mb-4 border-safe/40 bg-safe/5">
              <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-5">
                <div>
                  <p className="text-sm font-semibold text-safe">Your software supply chain is protected.</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Security Score {scanRun.security_score_before} → {scanRun.security_score_after} · Critical {scanRun.critical_before} → {scanRun.critical_after} ·
                    {" "}High {scanRun.high_before} → {scanRun.high_after} · Reachable {scanRun.reachable_before} → {scanRun.reachable_after}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => navigate("/app/pull-requests")}>View Pull Requests</Button>
                  <Button size="sm" variant="outline" onClick={() => navigate("/app/reports")}>View Security Report</Button>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="space-y-2.5">
            {scanRun.executions.map((ex) => <AgentNode key={ex.id} ex={ex} />)}
          </div>
        </>
      )}
    </div>
  );
}
