import type {
  AgentExecution,
  Approval,
  ASTFinding,
  AuditLogEntry,
  DashboardSummary,
  DependencyGraph,
  LicenseFinding,
  Patch,
  PullRequestSummary,
  Repository,
  SBOMComponent,
  ScanRun,
  Vulnerability,
} from "@/types";

const BASE = "/api";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  health: () => request<{ status: string; github_configured: boolean; anthropic_configured: boolean }>("/health"),

  // Repositories
  listRepositories: () => request<Repository[]>("/repositories"),
  getRepository: (id: string) => request<Repository>(`/repositories/${id}`),
  createRepository: (url: string, name?: string) =>
    request<Repository>("/repositories", { method: "POST", body: JSON.stringify({ url, name }) }),
  ensureDemoRepository: () => request<Repository>("/repositories/demo-seed", { method: "POST" }),
  deleteRepository: (id: string) => request<void>(`/repositories/${id}`, { method: "DELETE" }),
  triggerScan: (id: string) => request<ScanRun>(`/repositories/${id}/scan`, { method: "POST" }),
  listScanRuns: (id: string) => request<ScanRun[]>(`/repositories/${id}/scan-runs`),
  latestScanRun: (id: string) => request<ScanRun>(`/repositories/${id}/scan-runs/latest`),
  getSbom: (id: string) => request<{ repository: Repository; components: SBOMComponent[] }>(`/repositories/${id}/sbom`),
  getSbomCycloneDx: (id: string) => request<Record<string, unknown>>(`/repositories/${id}/sbom/cyclonedx`),
  getDependencyGraph: (id: string) => request<DependencyGraph>(`/repositories/${id}/dependency-graph`),
  getAstFindings: (id: string) => request<ASTFinding[]>(`/repositories/${id}/ast-findings`),
  getLicenseFindings: (id: string) => request<LicenseFinding[]>(`/repositories/${id}/license-findings`),
  getRepoVulnerabilities: (id: string) => request<Vulnerability[]>(`/repositories/${id}/vulnerabilities`),

  // Vulnerabilities
  listVulnerabilities: (params?: { severity?: string; reachable?: boolean }) => {
    const qs = new URLSearchParams();
    if (params?.severity) qs.set("severity", params.severity);
    if (params?.reachable !== undefined) qs.set("reachable", String(params.reachable));
    const suffix = qs.toString() ? `?${qs}` : "";
    return request<Vulnerability[]>(`/vulnerabilities${suffix}`);
  },
  getVulnerability: (id: string) => request<Vulnerability>(`/vulnerabilities/${id}`),

  // Patches
  listPatches: (repositoryId?: string) =>
    request<Patch[]>(`/patches${repositoryId ? `?repository_id=${repositoryId}` : ""}`),
  getPatch: (id: string) => request<Patch>(`/patches/${id}`),
  rerunPatchTests: (id: string) => request<Patch>(`/patches/${id}/test`, { method: "POST" }),
  approvePatch: (id: string) => request<Patch>(`/patches/${id}/approve`, { method: "POST" }),
  rejectPatch: (id: string) => request<Patch>(`/patches/${id}/reject`, { method: "POST" }),

  // Pull Requests
  listPullRequests: (repositoryId?: string) =>
    request<PullRequestSummary[]>(`/pull-requests${repositoryId ? `?repository_id=${repositoryId}` : ""}`),
  getPullRequest: (id: string) => request<PullRequestSummary>(`/pull-requests/${id}`),
  createPullRequest: (patchId: string) =>
    request<PullRequestSummary>("/pull-requests", { method: "POST", body: JSON.stringify({ patch_id: patchId }) }),

  // Agents
  listAgentDefinitions: () => request<{ name: string; order: number }[]>("/agents"),
  listExecutions: (params?: { scanRunId?: string; repositoryId?: string }) => {
    const qs = new URLSearchParams();
    if (params?.scanRunId) qs.set("scan_run_id", params.scanRunId);
    if (params?.repositoryId) qs.set("repository_id", params.repositoryId);
    const suffix = qs.toString() ? `?${qs}` : "";
    return request<AgentExecution[]>(`/agents/executions${suffix}`);
  },
  getScanRun: (id: string) => request<ScanRun>(`/agents/scan-runs/${id}`),

  // Audit logs
  listAuditLogs: (repositoryId?: string, limit = 200) =>
    request<AuditLogEntry[]>(`/audit-logs?limit=${limit}${repositoryId ? `&repository_id=${repositoryId}` : ""}`),

  // Reports
  getLatestReport: (repositoryId: string) => request<Record<string, any>>(`/reports/${repositoryId}`),
  getReportHistory: (repositoryId: string) => request<Record<string, any>[]>(`/reports/${repositoryId}/history`),

  // Approvals
  listApprovals: (params?: { repositoryId?: string; decision?: string }) => {
    const qs = new URLSearchParams();
    if (params?.repositoryId) qs.set("repository_id", params.repositoryId);
    if (params?.decision) qs.set("decision", params.decision);
    const suffix = qs.toString() ? `?${qs}` : "";
    return request<Approval[]>(`/approvals${suffix}`);
  },
  listPendingApprovals: () => request<Approval[]>("/approvals/pending"),
  decideApproval: (id: string, decision: "APPROVED" | "REJECTED", reasoning?: string) =>
    request<Approval>(`/approvals/${id}/decide`, {
      method: "POST",
      body: JSON.stringify({ decision, reasoning, decided_by: "security-lead" }),
    }),

  // Dashboard
  getDashboardSummary: () => request<DashboardSummary>("/dashboard/summary"),
};

export { ApiError };
