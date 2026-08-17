import * as React from "react";
import { Download, Boxes, Search } from "lucide-react";
import { useAppData } from "@/hooks/useAppData";
import { api } from "@/services/api";
import type { SBOMComponent } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export function SbomExplorerPage() {
  const { selectedRepoId, selectedRepo } = useAppData();
  const [components, setComponents] = React.useState<SBOMComponent[] | null>(null);
  const [search, setSearch] = React.useState("");
  const [ecosystemFilter, setEcosystemFilter] = React.useState("all");
  const [vulnOnly, setVulnOnly] = React.useState(false);

  React.useEffect(() => {
    if (!selectedRepoId) return;
    setComponents(null);
    api.getSbom(selectedRepoId).then((r) => setComponents(r.components));
  }, [selectedRepoId]);

  const ecosystems = React.useMemo(
    () => Array.from(new Set((components || []).map((c) => c.ecosystem))),
    [components]
  );

  const filtered = (components || []).filter((c) => {
    if (search && !c.name.toLowerCase().includes(search.toLowerCase())) return false;
    if (ecosystemFilter !== "all" && c.ecosystem !== ecosystemFilter) return false;
    if (vulnOnly && !c.is_vulnerable) return false;
    return true;
  });

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(components, null, 2)], { type: "application/json" });
    downloadBlob(blob, `${selectedRepo?.name || "sbom"}-sbom.json`);
  };

  const exportCycloneDx = async () => {
    if (!selectedRepoId) return;
    const data = await api.getSbomCycloneDx(selectedRepoId);
    downloadBlob(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }), `${selectedRepo?.name || "sbom"}-cyclonedx.json`);
  };

  const exportCsv = () => {
    const header = "Component,Version,Ecosystem,License,Direct/Transitive,Vulnerable,Reachable,Risk\n";
    const rows = filtered
      .map((c) => [c.name, c.version, c.ecosystem, c.license, c.is_direct ? "Direct" : "Transitive", c.is_vulnerable, c.is_reachable, c.risk_score].join(","))
      .join("\n");
    downloadBlob(new Blob([header + rows], { type: "text/csv" }), `${selectedRepo?.name || "sbom"}.csv`);
  };

  return (
    <div>
      <PageHeader
        title="SBOM Explorer"
        description={selectedRepo ? `${selectedRepo.total_dependencies} components in ${selectedRepo.name}` : "Select a repository"}
        actions={
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={exportJson}><Download className="h-3.5 w-3.5" /> JSON</Button>
            <Button size="sm" variant="outline" onClick={exportCycloneDx}><Download className="h-3.5 w-3.5" /> CycloneDX</Button>
            <Button size="sm" variant="outline" onClick={exportCsv}><Download className="h-3.5 w-3.5" /> CSV</Button>
          </div>
        }
      />

      <div className="mb-4 flex flex-wrap gap-2">
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search components…" className="w-56 pl-8" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <Select value={ecosystemFilter} onValueChange={setEcosystemFilter}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Ecosystem" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All ecosystems</SelectItem>
            {ecosystems.map((e) => <SelectItem key={e} value={e}>{e}</SelectItem>)}
          </SelectContent>
        </Select>
        <Button size="sm" variant={vulnOnly ? "default" : "outline"} onClick={() => setVulnOnly((v) => !v)}>
          Vulnerable only
        </Button>
      </div>

      {!components ? (
        <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
      ) : filtered.length === 0 ? (
        <EmptyState icon={Boxes} title="No components found" description="Run a scan to generate an SBOM, or adjust your filters." />
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Component</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Ecosystem</TableHead>
                <TableHead>License</TableHead>
                <TableHead>Scope</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Flags</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">{c.name}</TableCell>
                  <TableCell className="mono-tabular text-sm text-muted-foreground">
                    {c.version} {c.is_outdated && <span className="text-medium">→ {c.latest_version}</span>}
                  </TableCell>
                  <TableCell><Badge variant="muted">{c.ecosystem}</Badge></TableCell>
                  <TableCell className="text-sm">{c.license}</TableCell>
                  <TableCell>
                    <Badge variant={c.is_direct ? "outline" : "muted"}>{c.is_direct ? "Direct" : "Transitive"}</Badge>
                  </TableCell>
                  <TableCell className="mono-tabular text-sm">{c.risk_score || "—"}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {c.is_vulnerable && <Badge variant="critical">Vulnerable</Badge>}
                      {c.is_reachable && <Badge variant="high">Reachable</Badge>}
                      {c.is_suspicious && <Badge variant="high">Suspicious</Badge>}
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

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
