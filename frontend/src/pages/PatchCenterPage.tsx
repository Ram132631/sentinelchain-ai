import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Wrench, CheckCircle2, XCircle, FlaskConical, GitPullRequest, Loader2 } from "lucide-react";
import { useAppData } from "@/hooks/useAppData";
import { api } from "@/services/api";
import type { Patch } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";

const APPROVAL_VARIANT: Record<string, "success" | "critical" | "medium" | "muted"> = {
  APPROVED: "success",
  REJECTED: "critical",
  NEEDS_HUMAN_REVIEW: "medium",
  PENDING: "muted",
};

function DiffView({ diff }: { diff: string }) {
  const lines = diff.split("\n").filter((l) => !l.startsWith("---") && !l.startsWith("+++") && !l.startsWith("@@"));
  return (
    <pre className="overflow-x-auto rounded-md border border-border bg-black/40 p-3 font-mono text-xs leading-relaxed">
      {lines.map((line, i) => (
        <div
          key={i}
          className={
            line.startsWith("+") ? "bg-emerald-500/10 text-emerald-400" :
            line.startsWith("-") ? "bg-red-500/10 text-red-400" : "text-muted-foreground"
          }
        >
          {line || " "}
        </div>
      ))}
    </pre>
  );
}

function PatchCard({ patch, onChanged }: { patch: Patch; onChanged: () => void }) {
  const [busy, setBusy] = React.useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  const act = async (fn: () => Promise<any>, msg: string) => {
    setBusy(true);
    try {
      await fn();
      toast({ title: msg });
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>{patch.component_name}</CardTitle>
          <p className="mono-tabular mt-1 text-xs text-muted-foreground">
            {patch.current_version} → <span className="text-safe">{patch.target_version}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={patch.breaking_change_risk === "HIGH" ? "high" : patch.breaking_change_risk === "MEDIUM" ? "medium" : "safe"}>
            {patch.breaking_change_risk} RISK
          </Badge>
          <Badge variant={APPROVAL_VARIANT[patch.security_approval]}>{patch.security_approval.replace(/_/g, " ")}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="mb-3 text-xs text-muted-foreground">{patch.explanation}</p>

        <div className="mb-3 flex items-center gap-4 text-xs">
          <span>Risk before: <span className="font-semibold text-critical">{patch.risk_before}</span></span>
          <span>Risk after: <span className="font-semibold text-safe">{patch.risk_after}</span></span>
        </div>

        <DiffView diff={patch.diff_text} />

        {patch.test_results.length > 0 && (
          <div className="mt-3">
            <p className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
              <FlaskConical className="h-3.5 w-3.5" /> Test Results
            </p>
            <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
              {patch.test_results.map((t) => (
                <div key={t.id} className="flex items-center justify-between rounded-md border border-border bg-muted/30 px-2 py-1.5 text-[11px]">
                  <span>{t.test_type.replace(/_/g, " ")}{t.simulated && <span className="text-muted-foreground"> (sim)</span>}</span>
                  {t.status === "PASS" ? <CheckCircle2 className="h-3.5 w-3.5 text-safe" /> : <XCircle className="h-3.5 w-3.5 text-critical" />}
                </div>
              ))}
            </div>
          </div>
        )}

        {patch.auditor_notes && (
          <p className="mt-3 rounded-md border border-border bg-muted/20 p-2 text-[11px] text-muted-foreground">{patch.auditor_notes}</p>
        )}

        <div className="mt-4 flex flex-wrap gap-2">
          <Button size="sm" variant="outline" disabled={busy} onClick={() => act(() => api.rerunPatchTests(patch.id), "Tests re-run")}>
            {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FlaskConical className="h-3.5 w-3.5" />} Run Tests
          </Button>
          {patch.security_approval !== "APPROVED" && (
            <Button size="sm" variant="success" disabled={busy} onClick={() => act(() => api.approvePatch(patch.id), "Patch approved")}>
              <CheckCircle2 className="h-3.5 w-3.5" /> Approve
            </Button>
          )}
          {patch.security_approval !== "REJECTED" && (
            <Button size="sm" variant="destructive" disabled={busy} onClick={() => act(() => api.rejectPatch(patch.id), "Patch rejected")}>
              <XCircle className="h-3.5 w-3.5" /> Reject
            </Button>
          )}
          {patch.security_approval === "APPROVED" && patch.pull_requests.length === 0 && (
            <Button size="sm" disabled={busy} onClick={() => act(() => api.createPullRequest(patch.id), "Pull request prepared")}>
              <GitPullRequest className="h-3.5 w-3.5" /> Create PR
            </Button>
          )}
          {patch.pull_requests.length > 0 && (
            <Button size="sm" variant="ghost" onClick={() => navigate("/app/pull-requests")}>
              <GitPullRequest className="h-3.5 w-3.5" /> View PR #{patch.pull_requests[0].pr_number || "DEMO"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function PatchCenterPage() {
  const { selectedRepoId } = useAppData();
  const [patches, setPatches] = React.useState<Patch[] | null>(null);

  const load = React.useCallback(() => {
    if (!selectedRepoId) return;
    api.listPatches(selectedRepoId).then(setPatches);
  }, [selectedRepoId]);

  React.useEffect(() => { setPatches(null); load(); }, [load]);

  return (
    <div>
      <PageHeader title="Patch Center" description="Generated fixes with diffs, risk reduction, and test results." />

      {!patches ? (
        <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-56" />)}</div>
      ) : patches.length === 0 ? (
        <EmptyState icon={Wrench} title="No patches generated yet" description="Run a security scan — the Patch Generator agent creates fixes for vulnerabilities with an available vendor version." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {patches.map((p) => <PatchCard key={p.id} patch={p} onChanged={load} />)}
        </div>
      )}
    </div>
  );
}
