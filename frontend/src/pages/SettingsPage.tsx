import * as React from "react";
import { KeyRound, ShieldCheck, Github, Sparkles, Info } from "lucide-react";
import { api } from "@/services/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

export function SettingsPage() {
  const [health, setHealth] = React.useState<{ github_configured: boolean; anthropic_configured: boolean } | null>(null);

  React.useEffect(() => {
    api.health().then(setHealth);
  }, []);

  return (
    <div className="max-w-3xl">
      <PageHeader title="Settings" description="Credentials, tool integrations, and security policy for this deployment." />

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5"><Github className="h-4 w-4" /> GitHub Integration</CardTitle>
            <CardDescription>Used for repository metadata, manifest parsing, and DEMO-labeled PR preparation.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between rounded-md border border-border bg-muted/20 p-3">
              <span className="text-sm">GITHUB_TOKEN</span>
              <Badge variant={health?.github_configured ? "success" : "muted"}>
                {health?.github_configured ? "Configured" : "Not configured — public repos still work, rate-limited"}
              </Badge>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Set <code className="rounded bg-muted px-1 py-0.5">GITHUB_TOKEN</code> in <code className="rounded bg-muted px-1 py-0.5">backend/.env</code> to
              raise API rate limits and access private repositories. Tokens are never echoed back to the frontend or logs.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5"><Sparkles className="h-4 w-4" /> Anthropic Claude</CardTitle>
            <CardDescription>Powers natural-language explanations for risk and patch reasoning.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between rounded-md border border-border bg-muted/20 p-3">
              <span className="text-sm">ANTHROPIC_API_KEY</span>
              <Badge variant={health?.anthropic_configured ? "success" : "muted"}>
                {health?.anthropic_configured ? "Configured" : "Not configured — using deterministic rule-based explanations"}
              </Badge>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Absent a key, every AI-explanation surface in this app falls back to a deterministic, template-based
              explanation built from the same structured risk data — the platform never crashes or shows placeholder text.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5"><ShieldCheck className="h-4 w-4" /> Security Posture</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            {[
              "Sandboxed repository scanning — reads via GitHub API only, no arbitrary host command execution",
              "Secure subprocess wrapper for optional CLI tools (fixed argv, no shell=True, timeouts enforced)",
              "GitHub tokens and API keys are masked and never returned in API responses or logs",
              "Repository size and file-count limits enforced before any analysis begins",
              "Critical-severity or production-dependency patches always require explicit human approval",
              "Full audit trail: every autonomous action is recorded with timestamp, agent, input, and output",
            ].map((item) => (
              <div key={item} className="flex items-start gap-2">
                <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                <span>{item}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5"><KeyRound className="h-4 w-4" /> License Policy</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <span className="text-sm">Active policy</span>
              <Badge variant="outline">permissive-only</Badge>
            </div>
            <Separator className="my-3" />
            <p className="text-xs text-muted-foreground">
              GPL/AGPL and other strong-copyleft dependencies are flagged as policy violations. Weak-copyleft and
              unknown licenses are flagged for review. Change this in <code className="rounded bg-muted px-1 py-0.5">backend/app/demo_data/commerce_api.py</code> or
              extend the License Compliance agent to read a per-repository policy.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
