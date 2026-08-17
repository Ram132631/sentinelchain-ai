import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Play, Boxes, ShieldAlert, GitBranch, Loader2 } from "lucide-react";
import { useAppData } from "@/hooks/useAppData";
import { api } from "@/services/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/EmptyState";
import { RiskBandLabel } from "@/components/RiskScore";
import { formatRelativeTime } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";

const STATUS_VARIANT: Record<string, "muted" | "info" | "success" | "critical"> = {
  UNSCANNED: "muted",
  SCANNING: "info",
  SCANNED: "success",
  ERROR: "critical",
};

export function RepositoriesPage() {
  const { repositories, refreshRepositories, setSelectedRepoId } = useAppData();
  const [open, setOpen] = React.useState(false);
  const [url, setUrl] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [scanningId, setScanningId] = React.useState<string | null>(null);
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleAdd = async () => {
    if (!url.trim()) return;
    setSubmitting(true);
    try {
      const repo = await api.createRepository(url.trim());
      await refreshRepositories();
      setSelectedRepoId(repo.id);
      setOpen(false);
      setUrl("");
      toast({ title: "Repository added", description: repo.full_name, variant: "success" });
    } catch (e: any) {
      toast({ title: "Could not add repository", description: e.message, variant: "error" });
    } finally {
      setSubmitting(false);
    }
  };

  const handleScan = async (id: string) => {
    setScanningId(id);
    try {
      await api.triggerScan(id);
      setSelectedRepoId(id);
      toast({ title: "Scan started" });
      navigate("/app/agents");
    } finally {
      setScanningId(null);
    }
  };

  return (
    <div>
      <PageHeader
        title="Repositories"
        description="Connect GitHub repositories or use the built-in DEMO MODE sample."
        actions={
          <Button onClick={() => setOpen(true)}>
            <Plus className="h-4 w-4" /> Add Repository
          </Button>
        }
      />

      {repositories.length === 0 ? (
        <EmptyState icon={GitBranch} title="No repositories yet" description="Add a GitHub repository or reload to seed the demo repository." />
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Repository</TableHead>
                <TableHead>Language</TableHead>
                <TableHead>Last Scan</TableHead>
                <TableHead>Dependencies</TableHead>
                <TableHead>Critical Issues</TableHead>
                <TableHead>Risk Score</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {repositories.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{r.name}</span>
                      {r.is_demo && <Badge variant="info">DEMO</Badge>}
                    </div>
                    <p className="text-xs text-muted-foreground">{r.full_name}</p>
                  </TableCell>
                  <TableCell className="text-sm">{r.primary_language || "—"}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{formatRelativeTime(r.last_scan_at)}</TableCell>
                  <TableCell className="mono-tabular text-sm">{r.total_dependencies || "—"}</TableCell>
                  <TableCell className="mono-tabular text-sm">
                    {r.critical_count > 0 ? <span className="text-critical font-semibold">{r.critical_count}</span> : "0"}
                  </TableCell>
                  <TableCell>{r.risk_score ? <RiskBandLabel score={r.risk_score} invert /> : "—"}</TableCell>
                  <TableCell>
                    <Badge variant={STATUS_VARIANT[r.status] ?? "muted"}>{r.status}</Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1.5">
                      <Button size="sm" variant="outline" onClick={() => handleScan(r.id)} disabled={scanningId === r.id}>
                        {scanningId === r.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                        Scan
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => { setSelectedRepoId(r.id); navigate("/app/sbom"); }}>
                        <Boxes className="h-3.5 w-3.5" /> SBOM
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => { setSelectedRepoId(r.id); navigate("/app/vulnerabilities"); }}>
                        <ShieldAlert className="h-3.5 w-3.5" /> Analyze
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Repository</DialogTitle>
            <DialogDescription>
              Paste a public GitHub repository URL. If it can't be reached (no token, private, offline), the
              scan will clearly fall back to DEMO MODE data.
            </DialogDescription>
          </DialogHeader>
          <Input
            placeholder="https://github.com/owner/repo"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button onClick={handleAdd} disabled={submitting || !url.trim()}>
              {submitting && <Loader2 className="h-4 w-4 animate-spin" />} Add Repository
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
