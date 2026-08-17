import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, GitBranch, Boxes, Network, ShieldAlert, Crosshair,
  Bot, Wrench, GitPullRequest, FileText, ScrollText, Settings, ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/app", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/app/repositories", label: "Repositories", icon: GitBranch },
  { to: "/app/sbom", label: "SBOM Explorer", icon: Boxes },
  { to: "/app/graph", label: "Dependency Graph", icon: Network },
  { to: "/app/vulnerabilities", label: "Vulnerabilities", icon: ShieldAlert },
  { to: "/app/reachability", label: "Reachability", icon: Crosshair },
  { to: "/app/agents", label: "AI Agents", icon: Bot },
  { to: "/app/patches", label: "Patch Center", icon: Wrench },
  { to: "/app/pull-requests", label: "Pull Requests", icon: GitPullRequest },
  { to: "/app/reports", label: "Security Reports", icon: FileText },
  { to: "/app/audit-logs", label: "Audit Logs", icon: ScrollText },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-card/40 md:flex">
      <div className="flex h-14 items-center gap-2 border-b border-border px-4">
        <ShieldCheck className="h-5 w-5 text-primary" />
        <span className="text-sm font-bold tracking-tight">
          Sentinel<span className="text-gradient">Chain</span> AI
        </span>
      </div>
      <nav className="flex-1 space-y-0.5 overflow-y-auto p-2">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
                isActive && "bg-primary/10 text-primary"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-border p-3">
        <div className="rounded-md border border-border bg-muted/40 p-2.5 text-[11px] leading-snug text-muted-foreground">
          Sandboxed scanning · No arbitrary host execution · Human approval required for critical changes
        </div>
      </div>
    </aside>
  );
}
