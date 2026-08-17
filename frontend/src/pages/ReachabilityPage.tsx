import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Crosshair, ArrowDown } from "lucide-react";
import { useAppData } from "@/hooks/useAppData";
import { api } from "@/services/api";
import type { Vulnerability } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge, SeverityBadge } from "@/components/ui/badge";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function ReachabilityPage() {
  const { selectedRepoId } = useAppData();
  const [vulns, setVulns] = React.useState<Vulnerability[] | null>(null);
  const [filter, setFilter] = React.useState<"ALL" | "REACHABLE" | "NOT_REACHABLE">("ALL");
  const navigate = useNavigate();

  React.useEffect(() => {
    if (!selectedRepoId) return;
    setVulns(null);
    api.getRepoVulnerabilities(selectedRepoId).then(setVulns);
  }, [selectedRepoId]);

  const analyzed = (vulns || []).filter((v) => v.reachability);
  const filtered = analyzed.filter((v) => {
    if (filter === "REACHABLE") return v.reachability?.is_reachable;
    if (filter === "NOT_REACHABLE") return !v.reachability?.is_reachable;
    return true;
  });

  return (
    <div>
      <PageHeader
        title="Reachability Analysis"
        description="Is the vulnerable code actually callable from an exposed entry point?"
      />

      <Tabs value={filter} onValueChange={(v) => setFilter(v as any)} className="mb-4">
        <TabsList>
          <TabsTrigger value="ALL">All ({analyzed.length})</TabsTrigger>
          <TabsTrigger value="REACHABLE">Reachable ({analyzed.filter((v) => v.reachability?.is_reachable).length})</TabsTrigger>
          <TabsTrigger value="NOT_REACHABLE">Not Reachable ({analyzed.filter((v) => !v.reachability?.is_reachable).length})</TabsTrigger>
        </TabsList>
      </Tabs>

      {!vulns ? (
        <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32" />)}</div>
      ) : filtered.length === 0 ? (
        <EmptyState icon={Crosshair} title="No reachability data" description="Run a scan to trace call paths from entry points to vulnerable code." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {filtered.map((v) => (
            <Card key={v.id} className="cursor-pointer" onClick={() => navigate(`/app/vulnerabilities/${v.id}`)}>
              <CardContent className="pt-5">
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{v.cve_id || v.ghsa_id}</span>
                    <SeverityBadge severity={v.severity} />
                  </div>
                  {v.reachability?.is_reachable ? (
                    <Badge variant="critical">REACHABLE</Badge>
                  ) : (
                    <Badge variant="safe">NOT REACHABLE</Badge>
                  )}
                </div>
                <div className="flex flex-col items-start gap-1">
                  {["CVE / GHSA", "Vulnerable package", v.reachability?.vulnerable_function || "Vulnerable function", "Application import", v.reachability?.entry_point || "No entry point found", "User-controlled input"]
                    .filter(Boolean)
                    .map((hop, i, arr) => (
                      <React.Fragment key={i}>
                        <span className="rounded-md border border-border bg-muted/40 px-2.5 py-1 text-[11px]">{hop}</span>
                        {i < arr.length - 1 && <ArrowDown className="ml-2 h-3 w-3 text-muted-foreground/50" />}
                      </React.Fragment>
                    ))}
                </div>
                <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{v.reachability?.explanation}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
