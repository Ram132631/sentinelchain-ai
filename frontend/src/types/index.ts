export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "SAFE";

export interface Repository {
  id: string;
  name: string;
  full_name: string;
  url: string;
  description: string | null;
  is_demo: boolean;
  primary_language: string | null;
  languages: string[];
  frameworks: string[];
  package_managers: string[];
  dependency_files: string[];
  file_count: number;
  default_branch: string;
  status: "UNSCANNED" | "SCANNING" | "SCANNED" | "ERROR";
  health_score: number;
  risk_score: number;
  risk_score_before: number | null;
  total_dependencies: number;
  direct_dependencies: number;
  transitive_dependencies: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  reachable_count: number;
  last_scan_at: string | null;
  created_at: string;
}

export interface SBOMComponent {
  id: string;
  repository_id: string;
  name: string;
  version: string;
  ecosystem: string;
  purl: string;
  license: string;
  is_direct: boolean;
  depth: number;
  latest_version: string | null;
  is_outdated: boolean;
  is_suspicious: boolean;
  suspicious_reason: string | null;
  is_vulnerable: boolean;
  is_reachable: boolean;
  risk_score: number;
  source_tool: string;
}

export interface ReachabilityResult {
  id: string;
  vulnerability_id: string;
  is_reachable: boolean;
  confidence: number;
  entry_point: string | null;
  vulnerable_function: string | null;
  call_path: string[];
  explanation: string;
  analysis_method: string;
}

export interface Vulnerability {
  id: string;
  repository_id: string;
  component_id: string;
  cve_id: string | null;
  ghsa_id: string | null;
  package_name: string;
  installed_version: string;
  fixed_version: string | null;
  affected_range: string;
  severity: Severity;
  cvss_score: number;
  summary: string;
  description: string;
  published_date: string | null;
  references: string[];
  exploit_available: boolean;
  is_production_dependency: boolean;
  risk_score: number;
  risk_explanation: string;
  status: string;
  source: string;
  repository_name: string | null;
  reachability: ReachabilityResult | null;
  ai_danger_explanation?: string;
  patches?: { id: string; target_version: string; status: string; security_approval: string }[];
}

export interface ASTFinding {
  id: string;
  repository_id: string;
  file_path: string;
  line: number;
  function_name: string | null;
  issue_type: string;
  severity: Severity;
  code_snippet: string;
  recommendation: string;
  rule_id: string;
  tool: string;
}

export interface LicenseFinding {
  id: string;
  repository_id: string;
  component_id: string;
  component_name: string;
  license: string;
  classification: "PERMISSIVE" | "WEAK_COPYLEFT" | "COPYLEFT" | "UNKNOWN";
  policy_violation: boolean;
  explanation: string;
}

export interface TestResult {
  id: string;
  patch_id: string;
  test_type: string;
  status: "PASS" | "FAIL";
  summary: string;
  details: string;
  simulated: boolean;
  duration_ms: number;
}

export interface PullRequestSummary {
  id: string;
  repository_id: string;
  patch_id: string;
  pr_number: number;
  title: string;
  description: string;
  branch_name: string;
  base_branch: string;
  files_changed: string[];
  status: string;
  is_demo: boolean;
  url: string | null;
  risk_before: number;
  risk_after: number;
  vulnerability_fixed: string;
  ai_explanation: string;
  created_at: string;
}

export interface Patch {
  id: string;
  repository_id: string;
  vulnerability_id: string;
  component_name: string;
  current_version: string;
  target_version: string;
  dependency_file: string;
  diff_text: string;
  explanation: string;
  breaking_change_risk: "LOW" | "MEDIUM" | "HIGH";
  breaking_change_reason: string;
  risk_before: number;
  risk_after: number;
  status: string;
  security_approval: "PENDING" | "APPROVED" | "REJECTED" | "NEEDS_HUMAN_REVIEW";
  auditor_notes: string;
  test_results: TestResult[];
  pull_requests: PullRequestSummary[];
  vulnerability: { cve_id: string | null; ghsa_id: string | null; severity: Severity } | null;
  created_at: string;
}

export interface AgentExecution {
  id: string;
  scan_run_id: string;
  repository_id: string;
  agent_name: string;
  step_order: number;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "WAITING_FOR_APPROVAL" | "REJECTED";
  current_task: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number;
  tools_used: string[];
  input_summary: string;
  output_summary: string;
  reasoning: string;
  confidence: number;
  error_message: string | null;
}

export interface ScanRun {
  id: string;
  repository_id: string;
  status: "RUNNING" | "COMPLETED" | "FAILED" | "WAITING_FOR_APPROVAL";
  is_demo: boolean;
  started_at: string;
  completed_at: string | null;
  security_score_before: number;
  security_score_after: number;
  critical_before: number;
  critical_after: number;
  high_before: number;
  high_after: number;
  reachable_before: number;
  reachable_after: number;
  current_step: string;
  error_message: string | null;
  executions: AgentExecution[];
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  repository_id: string | null;
  scan_run_id: string | null;
  agent_name: string;
  action: string;
  input_data: string;
  output_data: string;
  status: string;
  user_approval: boolean | null;
  severity: string;
}

export interface Approval {
  id: string;
  repository_id: string;
  patch_id: string | null;
  vulnerability_id: string | null;
  requested_at: string;
  decided_at: string | null;
  decision: "PENDING" | "APPROVED" | "REJECTED" | "NEEDS_REVIEW";
  risk_level: Severity;
  component_name: string;
  proposed_change: string;
  ai_reasoning: string;
  reasoning: string;
  decided_by: string;
}

export interface DashboardSummary {
  repositories_scanned: number;
  total_repositories: number;
  total_dependencies: number;
  critical_vulnerabilities: number;
  high_vulnerabilities: number;
  reachable_vulnerabilities: number;
  patches_available: number;
  patches_generated: number;
  average_risk_score: number;
  severity_distribution: Record<string, number>;
  ecosystem_distribution: Record<string, number>;
  vulnerabilities_by_repository: { repository: string; critical: number; high: number; medium: number; low: number; risk_score: number }[];
  patch_success_rate: number;
  risk_trend: { date: string; score_before: number; score_after: number }[];
}

export interface DependencyGraphNode {
  id: string;
  type: "application" | "package";
  name: string;
  version: string;
  ecosystem?: string;
  is_direct?: boolean;
  is_vulnerable?: boolean;
  is_reachable?: boolean;
  is_suspicious?: boolean;
  risk_score?: number;
  license?: string;
  vulnerabilities?: Vulnerability[];
}

export interface DependencyGraphEdge {
  source: string;
  target: string;
}

export interface DependencyGraph {
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
}
