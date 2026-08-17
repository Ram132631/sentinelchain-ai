import { Handle, Position } from "reactflow";
import { AlertTriangle, ShieldAlert, Package, Crosshair } from "lucide-react";
import { cn } from "@/lib/utils";

export interface PackageNodeData {
  name: string;
  version: string;
  ecosystem?: string;
  isRoot?: boolean;
  isVulnerable?: boolean;
  isReachable?: boolean;
  isSuspicious?: boolean;
  riskScore?: number;
  onClick?: () => void;
}

function riskBorder(data: PackageNodeData) {
  if (data.isReachable) return "border-critical/60 shadow-[0_0_0_1px_rgba(248,113,113,0.4)]";
  if (data.isVulnerable) return "border-high/50";
  if (data.isSuspicious) return "border-medium/60";
  return "border-border";
}

export function PackageNode({ data }: { data: PackageNodeData }) {
  if (data.isRoot) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-primary bg-primary/10 px-4 py-2.5 text-primary shadow-glow">
        <Handle type="source" position={Position.Bottom} className="!bg-primary" />
        <Package className="h-4 w-4" />
        <span className="text-sm font-bold">{data.name}</span>
      </div>
    );
  }

  return (
    <button
      onClick={data.onClick}
      className={cn(
        "flex min-w-[150px] flex-col gap-0.5 rounded-md border bg-card/90 px-3 py-2 text-left shadow-sm transition-transform hover:-translate-y-0.5",
        riskBorder(data)
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-border" />
      <Handle type="source" position={Position.Bottom} className="!bg-border" />
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-xs font-semibold">{data.name}</span>
        {data.isReachable ? (
          <Crosshair className="h-3 w-3 shrink-0 text-critical" />
        ) : data.isVulnerable ? (
          <ShieldAlert className="h-3 w-3 shrink-0 text-high" />
        ) : data.isSuspicious ? (
          <AlertTriangle className="h-3 w-3 shrink-0 text-medium" />
        ) : null}
      </div>
      <span className="mono-tabular text-[10px] text-muted-foreground">{data.version}</span>
    </button>
  );
}
