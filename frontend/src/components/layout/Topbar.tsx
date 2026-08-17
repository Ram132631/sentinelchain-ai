import { useNavigate } from "react-router-dom";
import { Github, Play, ShieldCheck, Loader2 } from "lucide-react";
import { useAppData } from "@/hooks/useAppData";
import { useScanRun } from "@/hooks/useScanRun";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/components/ui/toast";

export function Topbar() {
  const { repositories, selectedRepoId, selectedRepo, setSelectedRepoId, health } = useAppData();
  const { isActive, startScan } = useScanRun(selectedRepoId);
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleScan = async () => {
    if (!selectedRepoId) return;
    await startScan();
    toast({ title: "Autonomous security scan started", description: "13 agents are analyzing this repository.", variant: "default" });
    navigate("/app/agents");
  };

  return (
    <header className="flex h-14 items-center justify-between gap-3 border-b border-border bg-card/30 px-4">
      <div className="flex items-center gap-3">
        <Select value={selectedRepoId ?? undefined} onValueChange={setSelectedRepoId}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select repository" />
          </SelectTrigger>
          <SelectContent>
            {repositories.map((r) => (
              <SelectItem key={r.id} value={r.id}>
                {r.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {selectedRepo?.is_demo && <Badge variant="info">DEMO MODE</Badge>}
        {health && !health.github_configured && (
          <Badge variant="muted" className="hidden lg:inline-flex">
            GitHub token not configured
          </Badge>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={() => navigate("/app/repositories")}>
          <Github className="h-4 w-4" />
          Connect GitHub
        </Button>
        <Button size="sm" onClick={handleScan} disabled={!selectedRepoId || isActive}>
          {isActive ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          {isActive ? "Scan Running…" : "Run Security Scan"}
        </Button>
      </div>
    </header>
  );
}
