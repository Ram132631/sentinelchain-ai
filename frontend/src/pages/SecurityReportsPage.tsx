import * as React from "react";
import { FileText, Download } from "lucide-react";
import { useAppData } from "@/hooks/useAppData";
import { api } from "@/services/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { RiskScoreGauge } from "@/components/RiskScore";

export function SecurityReportsPage() {
  const { selectedRepoId, selectedRepo } = useAppData();
  const [report, setReport] = React.useState<any | null>(null);
  const [notFound, setNotFound] = React.useState(false);

  React.useEffect(() => {
    if (!selectedRepoId) return;
    setReport(null);
    setNotFound(false);
    api.getLatestReport(selectedRepoId).then(setReport).catch(() => setNotFound(true));
  }, [selectedRepoId]);

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedRepo?.name || "security"}-report.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (notFound) {
    return (
      <div>
        <PageHeader title="Security Reports" />
        <EmptyState icon={FileText} title="No report generated yet" description="Run a full autonomous security scan to generate an executive security report." />
      </div>
    );
  }

  if (!report) {
    return <div className="space-y-3"><Skeleton className="h-8 w-48" /><Skeleton className="h-64" /></div>;
  }

  return (
    <div>
      <PageHeader
        title="Security Reports"
        description={`Generated ${new Date(report.generated_at).toLocaleString()}${report.is_demo ? " · DEMO MODE" : ""}`}
        actions={
          <>
            <Button variant="outline" size="sm" onClick={exportJson}><Download className="h-3.5 w-3.5" /> Export JSON</Button>
            <Button size="sm" onClick={() => window.print()}><Download className="h-3.5 w-3.5" /> Download PDF</Button>
          </>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Executive Summary</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed text-muted-foreground">{report.executive_summary}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-around pt-5">
            <RiskScoreGauge score={report.score_before} label="Before" invert />
            <RiskScoreGauge score={report.score_after} label="After" invert />
          </CardContent>
        </Card>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>SBOM Summary</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-3 gap-3 text-center text-sm">
            <Stat label="Total" value={report.sbom_summary?.total_components} />
            <Stat label="Direct" value={report.sbom_summary?.direct} />
            <Stat label="Transitive" value={report.sbom_summary?.transitive} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Reachability Analysis</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 text-center text-sm">
            <Stat label="Reachable" value={report.reachability_analysis?.reachable_count} tone="text-critical" />
            <Stat label="Not Reachable" value={report.reachability_analysis?.not_reachable_count} tone="text-safe" />
          </CardContent>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader><CardTitle>License Compliance</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {report.license_compliance?.details?.filter((d: any) => d.violation).length ? (
            report.license_compliance.details.filter((d: any) => d.violation).map((d: any, i: number) => (
              <div key={i} className="rounded-md border border-medium/30 bg-medium/5 p-2.5 text-xs">
                <span className="font-semibold">{d.component}</span> ({d.license}): {d.explanation}
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No license policy violations detected.</p>
          )}
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader><CardTitle>Security Recommendations</CardTitle></CardHeader>
        <CardContent>
          <ul className="list-inside list-disc space-y-1.5 text-sm text-muted-foreground">
            {report.security_recommendations?.map((r: string, i: number) => <li key={i}>{r}</li>)}
          </ul>
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader><CardTitle>Generated Patches</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {report.generated_patches?.map((p: any, i: number) => (
            <div key={i} className="flex items-center justify-between rounded-md border border-border bg-muted/20 p-2.5 text-xs">
              <span className="font-medium">{p.package}: {p.from} → {p.to}</span>
              <div className="flex items-center gap-3">
                <span className="mono-tabular">{p.risk_before} → {p.risk_after}</span>
                <Badge variant={p.security_approval === "APPROVED" ? "success" : "muted"}>{p.security_approval}</Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: any; tone?: string }) {
  return (
    <div>
      <p className={`mono-tabular text-xl font-bold ${tone ?? ""}`}>{value ?? "—"}</p>
      <p className="mt-1 text-[11px] text-muted-foreground">{label}</p>
    </div>
  );
}
