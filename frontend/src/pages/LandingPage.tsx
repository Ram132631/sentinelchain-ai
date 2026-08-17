import { Link } from "react-router-dom";
import {
  ShieldCheck, ArrowRight, GitBranch, Boxes, Crosshair, Wrench, FlaskConical,
  GitPullRequest, Bot, Users, ScrollText, Sparkles, Search,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const WORKFLOW = [
  { label: "Repository", icon: GitBranch },
  { label: "SBOM", icon: Boxes },
  { label: "CVE Intelligence", icon: Search },
  { label: "Reachability", icon: Crosshair },
  { label: "AI Patch", icon: Wrench },
  { label: "Automated Tests", icon: FlaskConical },
  { label: "Secure Pull Request", icon: GitPullRequest },
];

const FEATURES = [
  {
    icon: Boxes,
    title: "AI-Powered SBOM Intelligence",
    description: "Every scan generates a complete, CycloneDX-compatible Software Bill of Materials — direct and transitive dependencies, licenses, and versions.",
  },
  {
    icon: Crosshair,
    title: "Reachability-Based Risk",
    description: "Not every CVE matters equally. We trace whether the vulnerable function is actually callable from an exposed entry point before we call it urgent.",
  },
  {
    icon: Wrench,
    title: "Self-Healing Dependencies",
    description: "The platform generates minimal, explained version bumps — with a real diff, breaking-change analysis, and automated validation.",
  },
  {
    icon: Bot,
    title: "Autonomous Security Agents",
    description: "13 specialized agents — from repository scanning to documentation — communicate through shared state and a visible audit trail.",
  },
  {
    icon: Users,
    title: "Human-in-the-Loop Approval",
    description: "Critical vulnerabilities and production-dependency changes always stop for explicit human sign-off. No silent auto-merges.",
  },
  {
    icon: ScrollText,
    title: "Complete Auditability",
    description: "Every autonomous action — input, output, timestamp, agent, and approval — is recorded and reviewable.",
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-primary" />
            <span className="text-base font-bold tracking-tight">
              Sentinel<span className="text-gradient">Chain</span> AI
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" asChild>
              <Link to="/app">Launch Security Console</Link>
            </Button>
            <Button size="sm" asChild>
              <Link to="/app">
                Run Demo <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[560px] bg-[radial-gradient(ellipse_at_top,_hsla(189,94%,48%,0.14),transparent_60%)]" />
        <div className="mx-auto max-w-5xl px-6 pb-20 pt-24 text-center">
          <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            Multi-agent AI · Full DEMO MODE · No credentials required
          </div>
          <h1 className="text-balance text-4xl font-extrabold tracking-tight sm:text-5xl">
            Autonomous Security for the <span className="text-gradient">Modern Software Supply Chain</span>
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-balance text-base text-muted-foreground sm:text-lg">
            AI agents continuously discover, analyze, prioritize, patch, test and secure your software
            dependencies — end to end, with a human always in the loop for critical decisions.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Button size="lg" asChild>
              <Link to="/app">
                Launch Security Console <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link to="/app/agents">Run Demo</Link>
            </Button>
          </div>
        </div>

        <div className="mx-auto max-w-6xl px-6 pb-24">
          <div className="glass overflow-x-auto rounded-xl p-6">
            <div className="flex min-w-[720px] items-center justify-between gap-2">
              {WORKFLOW.map((step, i) => (
                <div key={step.label} className="flex flex-1 items-center gap-2">
                  <div className="flex flex-1 flex-col items-center gap-2 text-center">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full border border-primary/30 bg-primary/10 text-primary">
                      <step.icon className="h-4 w-4" />
                    </div>
                    <span className="text-[11px] font-medium text-muted-foreground">{step.label}</span>
                  </div>
                  {i < WORKFLOW.length - 1 && <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground/40" />}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-28">
        <div className="mb-10 text-center">
          <h2 className="text-2xl font-bold tracking-tight">Detect. Understand. Fix. Verify. Secure.</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Everything a security team needs to keep an autonomous handle on supply-chain risk.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <Card key={f.title}>
              <CardContent className="pt-5">
                <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <f.icon className="h-4.5 w-4.5" />
                </div>
                <h3 className="text-sm font-semibold">{f.title}</h3>
                <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{f.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <footer className="border-t border-border py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 text-xs text-muted-foreground sm:flex-row">
          <span>© 2026 SentinelChain AI — Hackathon build. DEMO MODE data is clearly labeled throughout.</span>
          <span>Detect. Understand. Fix. Verify. Secure.</span>
        </div>
      </footer>
    </div>
  );
}
