import * as React from "react";
import { useNavigate } from "react-router-dom";
import {
  GitBranch, Boxes, ShieldAlert, Flame, Crosshair, Wrench, Play, Loader2, TrendingUp,
} from "lucide-react";
import { useAppData } from "@/hooks/useAppData";
import { useScanRun } from "@/hooks/useScanRun";
import { api } from "@/services/api";
import type { DashboardSummary } from "@/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { SeverityDistributionChart } from "@/components/charts/SeverityDistributionChart";
import { RiskTrendChart } from "@/components/charts/RiskTrendChart";
import { EcosystemDistributionChart } from "@/components/charts/EcosystemDistributionChart";
import { VulnsByRepoChart } from "@/components/charts/VulnsByRepoChart";
import { useToast } from "@/components/ui/toast";

function StatCard({ icon: Icon, label, value, tone }: { icon: any; label: string; value: React.ReactNode; tone?: string }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 pt-5">
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted ${tone ?? "text-primary"}`}>
          <Icon className="h-4.5 w-4.5" />
        </div>
        <div>
          <p className="mono-tabular text-xl font-bold leading-none">{value}</p>
          <p className="mt-1 text-[11px] text-muted-foreground">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const { selectedRepoId, selectedRepo } = useAppData();
  const { isActive, startScan, scanRun } = useScanRun(selectedRepoId);
  const [summary, setSummary] = React.useState<DashboardSummary | null>(null);
  const navigate = useNavigate();
  const { toast } = useToast();

  const loadSummary = React.useCallback(() => {
    api.getDashboardSummary().then(setSummary).catch(() => setSummary(null));
  }, []);

  React.useEffect(() => {
    loadSummary();
    const interval = setInterval(loadSummary, 4000);
    return () => clearInterval(interval);
  }, [loadSummary]);

  const handleScan = async () => {
    await startScan();
    toast({ title: "Autonomous security scan started" });
    navigate("/app/agents");
  };

  if (!summary) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Security Overview"
        description={selectedRepo ? `Currently focused on ${selectedRepo.name}` : "Connect or select a repository to begin"}
        actions={
          <Button onClick={handleScan} disabled={!selectedRepoId || isActive}>
            {isActive ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {isActive ? `Running: ${scanRun?.current_step || "…"}` : "Run Security Scan"}
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        <StatCard icon={GitBranch} label="Repositories Scanned" value={summary.repositories_scanned} />
        <StatCard icon={Boxes} label="Total Dependencies" value={summary.total_dependencies} />
        <StatCard icon={Flame} label="Critical Vulnerabilities" value={summary.critical_vulnerabilities} tone="text-critical" />
        <StatCard icon={ShieldAlert} label="High Vulnerabilities" value={summary.high_vulnerabilities} tone="text-high" />
        <StatCard icon={Crosshair} label="Reachable Vulnerabilities" value={summary.reachable_vulnerabilities} tone="text-critical" />
        <StatCard icon={Wrench} label="Patches Available" value={summary.patches_available} tone="text-primary" />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Vulnerability Severity Distribution</CardTitle>
            <CardDescription>Across all scanned repositories</CardDescription>
          </CardHeader>
          <CardContent>
            <SeverityDistributionChart data={summary.severity_distribution} />
            <div className="mt-2 flex flex-wrap justify-center gap-3 text-[11px] text-muted-foreground">
              {Object.entries(summary.severity_distribution).map(([k, v]) => (
                <span key={k}>{k}: <span className="font-semibold text-foreground">{v}</span></span>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5"><TrendingUp className="h-3.5 w-3.5" /> Risk Trend</CardTitle>
            <CardDescription>Security score before vs. after each autonomous scan</CardDescription>
          </CardHeader>
          <CardContent>
            <RiskTrendChart data={summary.risk_trend} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Dependency Ecosystem Distribution</CardTitle>
            <CardDescription>Package ecosystems detected in SBOMs</CardDescription>
          </CardHeader>
          <CardContent>
            <EcosystemDistributionChart data={summary.ecosystem_distribution} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Vulnerabilities by Repository</CardTitle>
            <CardDescription>Severity breakdown per repository</CardDescription>
          </CardHeader>
          <CardContent>
            <VulnsByRepoChart data={summary.vulnerabilities_by_repository} />
          </CardContent>
        </Card>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Card>
          <CardContent className="flex items-center justify-between pt-5">
            <div>
              <p className="text-xs text-muted-foreground">Patch Success Rate</p>
              <p className="mono-tabular mt-1 text-2xl font-bold text-primary">{summary.patch_success_rate}%</p>
            </div>
            <Wrench className="h-8 w-8 text-primary/40" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between pt-5">
            <div>
              <p className="text-xs text-muted-foreground">Average Repository Risk Score</p>
              <p className="mono-tabular mt-1 text-2xl font-bold">{summary.average_risk_score}</p>
            </div>
            <ShieldAlert className="h-8 w-8 text-muted-foreground/40" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
