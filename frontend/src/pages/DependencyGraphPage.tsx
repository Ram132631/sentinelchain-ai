import * as React from "react";
import ReactFlow, {
  Background, Controls, MiniMap, type Edge, type Node, useEdgesState, useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";
import { Network, Search, X } from "lucide-react";
import { useAppData } from "@/hooks/useAppData";
import { api } from "@/services/api";
import type { DependencyGraph, DependencyGraphNode } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { PackageNode } from "@/components/graph/PackageNode";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RiskBandLabel } from "@/components/RiskScore";
import { SeverityBadge } from "@/components/ui/badge";

const nodeTypes = { packageNode: PackageNode };

function layoutGraph(graph: DependencyGraph): { nodes: Node[]; edges: Edge[] } {
  const childrenByParent = new Map<string, string[]>();
  graph.edges.forEach((e) => {
    childrenByParent.set(e.source, [...(childrenByParent.get(e.source) || []), e.target]);
  });

  const depth = new Map<string, number>();
  depth.set("root", 0);
  const queue = ["root"];
  while (queue.length) {
    const id = queue.shift()!;
    const d = depth.get(id)!;
    for (const child of childrenByParent.get(id) || []) {
      if (!depth.has(child) || depth.get(child)! > d + 1) {
        depth.set(child, d + 1);
        queue.push(child);
      }
    }
  }

  const byDepth = new Map<number, string[]>();
  graph.nodes.forEach((n) => {
    const d = depth.get(n.id) ?? 3;
    byDepth.set(d, [...(byDepth.get(d) || []), n.id]);
  });

  const nodeById = new Map(graph.nodes.map((n) => [n.id, n]));
  const X_GAP = 190;
  const Y_GAP = 110;
  const nodes: Node[] = [];

  Array.from(byDepth.entries()).forEach(([d, ids]) => {
    const totalWidth = (ids.length - 1) * X_GAP;
    ids.forEach((id, i) => {
      const data = nodeById.get(id) as DependencyGraphNode;
      nodes.push({
        id,
        type: "packageNode",
        position: { x: i * X_GAP - totalWidth / 2, y: d * Y_GAP },
        data: {
          name: data.name,
          version: data.version,
          ecosystem: data.ecosystem,
          isRoot: data.type === "application",
          isVulnerable: data.is_vulnerable,
          isReachable: data.is_reachable,
          isSuspicious: data.is_suspicious,
          riskScore: data.risk_score,
        },
      });
    });
  });

  const edges: Edge[] = graph.edges.map((e, i) => {
    const target = nodeById.get(e.target);
    const critical = target?.is_reachable;
    return {
      id: `e${i}`,
      source: e.source,
      target: e.target,
      animated: !!critical,
      style: { stroke: critical ? "#f87171" : "hsl(217 33% 26%)", strokeWidth: critical ? 2 : 1.2 },
    };
  });

  return { nodes, edges };
}

export function DependencyGraphPage() {
  const { selectedRepoId, selectedRepo } = useAppData();
  const [graph, setGraph] = React.useState<DependencyGraph | null>(null);
  const [selected, setSelected] = React.useState<DependencyGraphNode | null>(null);
  const [search, setSearch] = React.useState("");
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  React.useEffect(() => {
    if (!selectedRepoId) return;
    setGraph(null);
    api.getDependencyGraph(selectedRepoId).then(setGraph);
  }, [selectedRepoId]);

  React.useEffect(() => {
    if (!graph) return;
    const { nodes: laidOutNodes, edges: laidOutEdges } = layoutGraph(graph);
    const withHandlers = laidOutNodes.map((n) => ({
      ...n,
      data: { ...n.data, onClick: () => setSelected(graph.nodes.find((g) => g.id === n.id) || null) },
      hidden: search ? !n.data.isRoot && !n.data.name.toLowerCase().includes(search.toLowerCase()) : false,
    }));
    setNodes(withHandlers);
    setEdges(laidOutEdges);
  }, [graph, search, setNodes, setEdges]);

  if (!selectedRepoId) return <EmptyState icon={Network} title="Select a repository" />;

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <PageHeader
        title="Dependency Graph"
        description={selectedRepo ? `${selectedRepo.total_dependencies} components visualized` : ""}
        actions={
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Search packages…" className="w-56 pl-8" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
        }
      />
      <div className="relative flex-1 overflow-hidden rounded-lg border border-border bg-card/30">
        {!graph ? (
          <div className="p-6"><Skeleton className="h-full min-h-[400px]" /></div>
        ) : graph.nodes.length === 0 ? (
          <EmptyState icon={Network} title="No dependency graph yet" description="Run a security scan to generate the dependency graph." className="h-full" />
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            minZoom={0.2}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="hsl(217 33% 20%)" gap={20} />
            <Controls showInteractive={false} />
            <MiniMap
              pannable
              zoomable
              maskColor="rgba(6,12,24,0.7)"
              nodeColor={(n) => (n.data?.isReachable ? "#f87171" : n.data?.isVulnerable ? "#fb923c" : "#334155")}
              style={{ background: "hsl(222 44% 8%)" }}
            />
          </ReactFlow>
        )}

        {selected && (
          <div className="glass absolute right-3 top-3 w-80 rounded-lg p-4 shadow-2xl">
            <div className="mb-3 flex items-start justify-between">
              <div>
                <p className="font-semibold">{selected.name}</p>
                <p className="mono-tabular text-xs text-muted-foreground">{selected.version}</p>
              </div>
              <button onClick={() => setSelected(null)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="space-y-2 text-xs">
              <Row label="Ecosystem" value={selected.ecosystem || "—"} />
              <Row label="License" value={selected.license || "—"} />
              <Row label="Risk" value={selected.risk_score !== undefined ? <RiskBandLabel score={selected.risk_score} /> : "—"} />
              <Row label="Reachable" value={selected.is_reachable ? <Badge variant="critical">YES</Badge> : <Badge variant="safe">NO</Badge>} />
            </div>
            {selected.vulnerabilities && selected.vulnerabilities.length > 0 && (
              <div className="mt-3 space-y-2 border-t border-border pt-3">
                <p className="text-[11px] font-semibold uppercase text-muted-foreground">Vulnerabilities</p>
                {selected.vulnerabilities.map((v) => (
                  <div key={v.id} className="rounded-md border border-border bg-muted/30 p-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium">{v.cve_id || v.ghsa_id}</span>
                      <SeverityBadge severity={v.severity} />
                    </div>
                    <p className="mt-1 text-[11px] text-muted-foreground">
                      Fixed version: <span className="text-foreground">{v.fixed_version || "unavailable"}</span>
                    </p>
                  </div>
                ))}
              </div>
            )}
            {selected.risk_score !== undefined && selected.risk_score > 40 && (
              <Button size="sm" className="mt-3 w-full" variant="outline" asChild>
                <a href="/app/patches">Recommended Action: Upgrade</a>
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
