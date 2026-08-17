import * as React from "react";
import { useNavigate } from "react-router-dom";
import { ShieldAlert, Search, Crosshair, Wrench } from "lucide-react";
import { useAppData } from "@/hooks/useAppData";
import { api } from "@/services/api";
import type { Vulnerability } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge, SeverityBadge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

const SEVERITIES = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"];

export function VulnerabilitiesPage() {
  const { selectedRepoId } = useAppData();
  const [vulns, setVulns] = React.useState<Vulnerability[] | null>(null);
  const [severity, setSeverity] = React.useState("ALL");
  const [search, setSearch] = React.useState("");
  const navigate = useNavigate();

  React.useEffect(() => {
    if (!selectedRepoId) return;
    setVulns(null);
    api.getRepoVulnerabilities(selectedRepoId).then(setVulns);
  }, [selectedRepoId]);

  const filtered = (vulns || []).filter((v) => {
    if (severity !== "ALL" && v.severity !== severity) return false;
    if (search && !`${v.package_name} ${v.cve_id} ${v.ghsa_id}`.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div>
      <PageHeader title="Vulnerability Center" description="Prioritized by practical risk, not just CVSS." />

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Tabs value={severity} onValueChange={setSeverity}>
          <TabsList>
            {SEVERITIES.map((s) => <TabsTrigger key={s} value={s}>{s}</TabsTrigger>)}
          </TabsList>
        </Tabs>
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search CVE or package…" className="w-64 pl-8" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      {!vulns ? (
        <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
      ) : filtered.length === 0 ? (
        <EmptyState icon={ShieldAlert} title="No vulnerabilities match" description="Run a scan or adjust your filters." />
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Severity</TableHead>
                <TableHead>CVE / GHSA</TableHead>
                <TableHead>Package</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>CVSS</TableHead>
                <TableHead>Reachability</TableHead>
                <TableHead>Fixed Version</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((v) => (
                <TableRow key={v.id} className="cursor-pointer" onClick={() => navigate(`/app/vulnerabilities/${v.id}`)}>
                  <TableCell><SeverityBadge severity={v.severity} /></TableCell>
                  <TableCell className="font-medium">{v.cve_id || v.ghsa_id}</TableCell>
                  <TableCell>{v.package_name}</TableCell>
                  <TableCell className="mono-tabular text-sm text-muted-foreground">{v.installed_version}</TableCell>
                  <TableCell className="mono-tabular text-sm">{v.cvss_score.toFixed(1)}</TableCell>
                  <TableCell>
                    {v.reachability ? (
                      v.reachability.is_reachable ? <Badge variant="critical">REACHABLE</Badge> : <Badge variant="safe">NOT REACHABLE</Badge>
                    ) : <Badge variant="muted">PENDING</Badge>}
                  </TableCell>
                  <TableCell className="mono-tabular text-sm">{v.fixed_version || "—"}</TableCell>
                  <TableCell><Badge variant="muted">{v.status}</Badge></TableCell>
                  <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex justify-end gap-1.5">
                      <Button size="sm" variant="ghost" onClick={() => navigate(`/app/vulnerabilities/${v.id}`)}>
                        <Crosshair className="h-3.5 w-3.5" /> Investigate
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => navigate("/app/patches")}>
                        <Wrench className="h-3.5 w-3.5" /> Patch
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
