import * as React from "react";
import { GitPullRequest, ExternalLink } from "lucide-react";
import { useAppData } from "@/hooks/useAppData";
import { api } from "@/services/api";
import type { PullRequestSummary } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";

function PrCard({ pr }: { pr: PullRequestSummary }) {
  const { toast } = useToast();
  return (
    <Card>
      <CardContent className="pt-5">
        <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <GitPullRequest className="h-4 w-4 text-primary" />
              <p className="font-semibold">{pr.title}</p>
            </div>
            <p className="mono-tabular mt-1 text-xs text-muted-foreground">
              {pr.is_demo ? "DEMO PR" : `PR #${pr.pr_number}`} · {pr.branch_name} → {pr.base_branch}
            </p>
          </div>
          <Badge variant="info">{pr.status.replace(/_/g, " ")}</Badge>
        </div>

        <div className="mb-3 grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
          <Info label="Vulnerability Fixed" value={pr.vulnerability_fixed || "—"} />
          <Info label="Risk Before" value={String(pr.risk_before)} tone="text-critical" />
          <Info label="Risk After" value={String(pr.risk_after)} tone="text-safe" />
          <Info label="Files Changed" value={String(pr.files_changed.length)} />
        </div>

        <p className="whitespace-pre-line rounded-md border border-border bg-muted/20 p-3 text-xs leading-relaxed text-muted-foreground">
          {pr.ai_explanation}
        </p>

        <div className="mt-3 flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              toast({
                title: pr.is_demo ? "DEMO PR — no external repository was modified" : "Opening pull request",
                description: pr.is_demo
                  ? "GitHub write access wasn't configured for this run, so this PR was prepared locally for review only."
                  : undefined,
              })
            }
          >
            <ExternalLink className="h-3.5 w-3.5" /> Open Pull Request
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function Info({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div>
      <p className="text-[10px] uppercase text-muted-foreground">{label}</p>
      <p className={`mono-tabular font-semibold ${tone ?? ""}`}>{value}</p>
    </div>
  );
}

export function PullRequestsPage() {
  const { selectedRepoId } = useAppData();
  const [prs, setPrs] = React.useState<PullRequestSummary[] | null>(null);

  React.useEffect(() => {
    if (!selectedRepoId) return;
    setPrs(null);
    api.listPullRequests(selectedRepoId).then(setPrs);
  }, [selectedRepoId]);

  return (
    <div>
      <PageHeader title="Pull Request Center" description="Autonomously prepared security fixes, ready for review." />
      {!prs ? (
        <div className="space-y-3">{Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-48" />)}</div>
      ) : prs.length === 0 ? (
        <EmptyState icon={GitPullRequest} title="No pull requests yet" description="Approved patches are automatically prepared into pull requests by the Release Manager agent." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {prs.map((pr) => <PrCard key={pr.id} pr={pr} />)}
        </div>
      )}
    </div>
  );
}
