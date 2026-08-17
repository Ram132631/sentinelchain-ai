import { Route, Routes } from "react-router-dom";
import { AppDataProvider } from "@/hooks/useAppData";
import { AppShell } from "@/layouts/AppShell";
import { LandingPage } from "@/pages/LandingPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { RepositoriesPage } from "@/pages/RepositoriesPage";
import { SbomExplorerPage } from "@/pages/SbomExplorerPage";
import { DependencyGraphPage } from "@/pages/DependencyGraphPage";
import { VulnerabilitiesPage } from "@/pages/VulnerabilitiesPage";
import { VulnerabilityDetailPage } from "@/pages/VulnerabilityDetailPage";
import { ReachabilityPage } from "@/pages/ReachabilityPage";
import { AgentMonitorPage } from "@/pages/AgentMonitorPage";
import { PatchCenterPage } from "@/pages/PatchCenterPage";
import { PullRequestsPage } from "@/pages/PullRequestsPage";
import { SecurityReportsPage } from "@/pages/SecurityReportsPage";
import { AuditLogsPage } from "@/pages/AuditLogsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

export default function App() {
  return (
    <AppDataProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="repositories" element={<RepositoriesPage />} />
          <Route path="sbom" element={<SbomExplorerPage />} />
          <Route path="graph" element={<DependencyGraphPage />} />
          <Route path="vulnerabilities" element={<VulnerabilitiesPage />} />
          <Route path="vulnerabilities/:id" element={<VulnerabilityDetailPage />} />
          <Route path="reachability" element={<ReachabilityPage />} />
          <Route path="agents" element={<AgentMonitorPage />} />
          <Route path="patches" element={<PatchCenterPage />} />
          <Route path="pull-requests" element={<PullRequestsPage />} />
          <Route path="reports" element={<SecurityReportsPage />} />
          <Route path="audit-logs" element={<AuditLogsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AppDataProvider>
  );
}
