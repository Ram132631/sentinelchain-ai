# SentinelChain AI

**Autonomous Software Supply Chain Security & Self-Healing SBOM Intelligence Platform**

> Detect. Understand. Fix. Verify. Secure.

SentinelChain AI is a multi-agent AI platform that continuously scans repositories, builds
a Software Bill of Materials, ingests real vulnerability intelligence, determines whether
vulnerable code is actually **reachable** from an exposed entry point, generates and tests
secure patches, and prepares pull requests — with a human always in the loop for critical
decisions.

---

## Table of Contents

1. [Problem & Solution](#problem--solution)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Multi-Agent Pipeline](#multi-agent-pipeline)
5. [Demo Mode](#demo-mode)
6. [Installation](#installation)
7. [Environment Variables](#environment-variables)
8. [Running Locally](#running-locally)
9. [Docker Setup](#docker-setup)
10. [API Reference](#api-reference)
11. [Security Considerations](#security-considerations)
12. [Testing](#testing)
13. [Future Improvements](#future-improvements)

---

## Problem & Solution

Modern applications pull in hundreds of open-source dependencies, each a potential vector for
zero-days, dependency-confusion attacks, malicious packages, and unpatched CVEs. Security
teams can't manually triage every advisory — and raw CVSS scores alone are a poor proxy for
*actual* risk: a 9.8-CVSS package that's never imported by a running service is far less
dangerous than a 7.5-CVSS package sitting directly behind an authenticated API route.

SentinelChain AI automates the full lifecycle — scan, SBOM, vulnerability intelligence, risk
prioritization, **reachability analysis**, patch generation, automated validation, security
audit, human approval, and pull-request preparation — while keeping every step explainable
and auditable.

## Architecture

```
Repository
   │
   ▼
Repository Scanner ──▶ SBOM Agent ──▶ Dependency Analyzer ──▶ Vulnerability Intelligence
   │                                                                    │
   ▼                                                                    ▼
Documentation Agent ◀── Release Manager ◀── [Human Approval] ◀── Security Auditor ◀── QA Validation ◀── Patch Generator ◀── License Compliance ◀── AST Code Analysis ◀── Reachability Analysis ◀── Risk Prioritization
```

A native async state-machine orchestrator (`backend/app/agents/orchestrator.py`) runs the 13
agents as sequential nodes, persisting every transition (`PENDING → RUNNING → COMPLETED /
FAILED / WAITING_FOR_APPROVAL / REJECTED`) to the database so the frontend's Agent Monitor and
Audit Log pages read live pipeline state — not mocked data. It mirrors the LangGraph workflow
described in the project spec, implemented without a hard `langgraph` runtime dependency so
the hackathon build has zero risk of breaking on an incompatible install (see
[Future Improvements](#future-improvements) for the drop-in migration path).

```
sentinelchain-ai/
├── frontend/           React + Vite + TypeScript + Tailwind + shadcn-style UI kit
│   └── src/
│       ├── pages/       Landing, Dashboard, Repositories, SBOM, Graph, Vulnerabilities,
│       │                 Reachability, Agent Monitor, Patch Center, PR Center, Reports, Audit
│       ├── components/  ui/ (button, card, badge, dialog, tabs…), charts/, graph/, layout/
│       ├── hooks/        useAppData (global repo context), useScanRun (live polling)
│       └── services/api.ts   typed fetch client for every backend endpoint
├── backend/             FastAPI + SQLAlchemy + Pydantic
│   └── app/
│       ├── agents/orchestrator.py      the 13-agent pipeline
│       ├── models/                     Repository, SBOMComponent, Vulnerability,
│       │                                ReachabilityResult, Patch, TestResult, PullRequest,
│       │                                ScanRun, AgentExecution, AuditLog, Approval, …
│       ├── scanners/    repo_scanner.py (GitHub API), source_fetcher.py
│       ├── sbom/         sbom_generator.py (package.json / lockfile / requirements.txt parser)
│       ├── vulnerability/osv_client.py  (real OSV.dev batch queries)
│       ├── reachability/ reachability_analyzer.py (curated demo call-graphs + AST/import heuristic)
│       ├── services/     ast_analysis.py, license_engine.py, risk_engine.py, explain.py
│       ├── patching/     patch_generator.py (semver diff + breaking-change assessment)
│       ├── testing/      qa_runner.py (structured validation suite)
│       ├── reports/      report_generator.py
│       ├── security/     validation.py, subprocess_utils.py
│       ├── demo_data/    commerce_api.py — the curated DEMO MODE dataset
│       └── api/          repositories, vulnerabilities, patches, pull_requests, agents,
│                          audit_logs, reports, approvals, dashboard
├── docker/               Dockerfiles + nginx.conf
├── docker-compose.yml
└── tests/, backend/tests/
```

## Technology Stack

**Frontend** — React 18, Vite, TypeScript, Tailwind CSS, a hand-built shadcn-style component
kit (Radix primitives + `class-variance-authority`), Lucide icons, Recharts, React Flow.

**Backend** — Python, FastAPI, Pydantic v2, SQLAlchemy 2.0 (SQLite by default; the models and
session layer are ORM-only so switching to PostgreSQL is a one-line `DATABASE_URL` change).

**AI / Agent layer** — a native async orchestrator implementing the same 13-node graph a
LangGraph `StateGraph` would express; `app/services/explain.py` calls Anthropic Claude when
`ANTHROPIC_API_KEY` is set and falls back to deterministic, template-based reasoning otherwise.

**Security / supply-chain integrations** — real GitHub REST API calls for repository metadata
and manifest content; real OSV.dev batch vulnerability queries (no auth required); a
manifest/lockfile parser as the SBOM fallback when `syft` isn't installed; a regex/AST static
scanner as the fallback when `semgrep` isn't installed; Python's built-in `ast` module for
reachability heuristics on `.py` sources.

## Multi-Agent Pipeline

| # | Agent | What it does |
|---|-------|---------------|
| 1 | Repository Scanner | Fetches real GitHub metadata + file tree (public repos, no token required); detects languages, package managers, dependency files |
| 2 | SBOM Agent | Parses `package.json` / `package-lock.json` / `requirements.txt` / `pyproject.toml` directly from GitHub, or falls back to the curated demo SBOM |
| 3 | Dependency Analyzer | Builds the parent → child dependency graph, flags outdated & suspicious (dependency-confusion-pattern) packages |
| 4 | Vulnerability Intelligence | Queries the real OSV.dev API in batch, or uses curated demo intelligence keyed to real GHSA/CVE IDs |
| 5 | Risk Prioritization | CVSS + exploitability + dependency importance + patch availability — **not CVSS alone** |
| 6 | Reachability Analysis | Traces CVE → vulnerable function → import → entry point → user input; recomputes final risk with the reachability signal |
| 7 | AST Code Analysis | `semgrep` if installed, else a real regex/AST fallback scanner for secrets, injection patterns, unsafe eval/exec |
| 8 | License Compliance | Classifies licenses (permissive / weak-copyleft / copyleft / unknown) against a configurable policy |
| 9 | Patch Generator | Minimal safe version bump, real unified diff, semver-based breaking-change risk |
| 10 | QA Validation | Security-fix verification, static re-scan, and SBOM diff are computed **for real**; full `npm test` execution is sandboxed/simulated and clearly labeled (see [Security Considerations](#security-considerations)) |
| 11 | Security Auditor | Rule-based APPROVED / NEEDS_HUMAN_REVIEW / REJECTED decision |
| 12 | Release Manager | Prepares a DEMO pull request (title, description, diff, evidence) — never pushes to a real external repo automatically |
| 13 | Documentation Agent | Generates the executive security report |

Between steps 11 and 12 sits a **human-approval gate**: any patch touching a CRITICAL-severity
vulnerability, a HIGH-severity production dependency, or a major-version (breaking-change) bump
is held for explicit approval via `/api/approvals/{id}/decide` — the pipeline cannot bypass it.

## Demo Mode

The platform works completely offline, with zero credentials. On first run it seeds a fictional
sample repository, **`demo-commerce-api`**, described as a Node/Express e-commerce backend with
a realistic, hand-curated dependency tree (express, lodash, axios, jsonwebtoken, mongoose, ejs,
moment, node-fetch, and transitive packages like `qs`, `follow-redirects`, `minimist`).

Its vulnerabilities reference **real, public GHSA/CVE advisories** (e.g. `CVE-2022-29078` for
ejs template injection, `CVE-2022-23529` for jsonwebtoken's key-confusion bug) attached to a
synthetic call-graph — so the reachability story is genuine and instructive (a CVSS-9.8
`minimist` prototype-pollution bug is marked **NOT REACHABLE** because it only runs at build
time, while a CVSS-7.5 `axios` bug *is* reachable because it sits on the checkout path).

Every demo-derived result is labeled **DEMO MODE** in the UI. Point the platform at a real
public GitHub repository and it will attempt genuine GitHub + OSV.dev calls, falling back to
demo data (with a clear reason shown) only when the network, token, or manifest can't be
resolved.

Click **"Run Demo"** on the landing page, or **"Run Security Scan"** anywhere in the console, to
watch all 13 agents execute in real time.

## Installation

**Prerequisites:** Python 3.11–3.13 (SQLAlchemy/pydantic-core prebuilt wheels aren't guaranteed
for brand-new Python releases — see the note below) and Node.js 18+.

```bash
git clone <this-repo>
cd sentinelchain-ai
```

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional — fill in GITHUB_TOKEN / ANTHROPIC_API_KEY if you have them
uvicorn app.main:app --reload --port 8000
```

> **Very new Python versions:** if `pip install` tries to compile `pydantic-core` from source
> and fails because no Rust/MSVC toolchain is available, it means no prebuilt wheel exists yet
> for your interpreter. Either use Python 3.11–3.13, or drop the version pins in
> `requirements.txt` and re-run `pip install` (newer releases typically ship wheels sooner).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173**. The Vite dev server proxies `/api/*` to `http://localhost:8000`
(see `frontend/vite.config.ts`).

## Environment Variables

All variables are optional — the platform runs fully in DEMO MODE with none of them set.

| Variable | Used by | Effect when unset |
|---|---|---|
| `GITHUB_TOKEN` | Repository Scanner, SBOM Agent | Public repos are still scanned (rate-limited); private repos and rate-limit failures fall back to DEMO MODE |
| `ANTHROPIC_API_KEY` | AI explainability (`app/services/explain.py`) | Deterministic, template-based explanations are used instead — never a crash or blank text |
| `DATABASE_URL` | SQLAlchemy engine | Defaults to a local SQLite file at `backend/data/sentinelchain.db`; set to a `postgresql+psycopg://…` URL to switch databases with no code changes |
| `CORS_ORIGINS` | FastAPI CORS middleware | Defaults to `http://localhost:5173` |

See `backend/.env.example` and the root `.env.example` (used by `docker-compose.yml`).

## Running Locally

```bash
# terminal 1
cd backend && uvicorn app.main:app --reload --port 8000
# terminal 2
cd frontend && npm run dev
```

Then: **Landing Page → Launch Security Console → Run Security Scan** — watch the 13-agent
pipeline execute, review the human-approval prompt for CRITICAL findings, approve or reject,
and see the prepared pull request, updated SBOM, and security report.

## Docker Setup

```bash
cp .env.example .env   # optional
docker compose up --build
```

- Backend: `http://localhost:8000` (SQLite data persisted in the `sentinelchain_data` volume)
- Frontend: `http://localhost:5173` (nginx, proxying `/api/*` to the backend container)

## API Reference

Interactive OpenAPI docs are served at **`/docs`** once the backend is running. Highlights:

```
POST   /api/repositories                       add a repository (GitHub URL)
POST   /api/repositories/{id}/scan              trigger the full 13-agent pipeline
GET    /api/repositories/{id}/sbom              components + repository summary
GET    /api/repositories/{id}/dependency-graph  nodes + edges for React Flow
GET    /api/vulnerabilities/{id}                full detail incl. reachability + AI reasoning
POST   /api/patches/{id}/approve|reject         human-in-the-loop decision on a specific patch
POST   /api/approvals/{id}/decide               decide a pending human-approval gate
GET    /api/agents/scan-runs/{id}               live agent execution states (poll this)
GET    /api/audit-logs                          full audit trail
GET    /api/reports/{repository_id}             latest generated security report
GET    /api/dashboard/summary                   executive dashboard aggregates
```

## Security Considerations

- **Sandboxed scanning.** Repositories are never cloned or executed on the host; only GitHub's
  read-only Contents/Trees API is used to fetch metadata and manifest text.
- **No arbitrary command execution.** `app/security/subprocess_utils.py` is the only path to an
  external CLI tool (`syft`/`grype`/`semgrep` if present) and enforces a fixed argv list,
  `shell=False`, and a timeout — never string-interpolated shell commands.
- **Path & size validation.** `app/security/validation.py` validates every GitHub URL, confines
  any on-disk workspace writes to a sandboxed directory, and enforces file-count/size limits.
- **Secrets are masked.** `app.config.mask_secret()` ensures tokens are never echoed in API
  responses or logs.
- **QA honesty.** The QA Validation agent runs real checks where it safely can (semver
  resolution against the advisory's fixed version, a static re-scan, an SBOM diff) and clearly
  labels `simulated: true` for the checks that would require executing arbitrary, untrusted
  repository code (`npm install && npm test`) — which this build intentionally does not do on
  the host. Wiring per-repository Docker sandboxes for real test execution is the natural next
  step (see below).
- **No autonomous external writes.** The Release Manager always prepares a DEMO pull request
  (diff, description, evidence) rather than pushing to a real repository — GitHub write access
  is out of scope for this hackathon build by design, not by omission.
- **Human-in-the-loop is not optional.** Any CRITICAL-severity or breaking-change patch is held
  at a database-level `WAITING_FOR_APPROVAL` gate; there is no code path that skips it.
- **Auditability.** Every agent transition and every human decision is written to `AuditLog`
  with a timestamp, agent name, action, and (for approvals) the reviewer's identity.

## Testing

```bash
cd backend
pytest tests/ -v
```

27 tests cover risk scoring (reachability changes the score, not just severity), license
classification and policy evaluation, semver-based patch risk assessment and diff generation,
SBOM manifest/lockfile parsing, the reachability heuristics (import + route correlation), and
FastAPI endpoint behavior (health, repository validation, 404s, dashboard shape) via
`TestClient`.

The full pipeline was additionally verified end-to-end in this environment: triggering a demo
scan, confirming all 13 agent states transition correctly, approving the human-review gate,
and validating the resulting SBOM, patches, pull requests, security report, and audit trail —
plus a Playwright-driven visual smoke test of every page with zero console errors.

## Future Improvements

- Swap the native orchestrator for an actual `langgraph.StateGraph` — the node/edge structure
  in `app/agents/orchestrator.py` was deliberately kept 1:1 with a LangGraph graph definition
  to make this a mechanical migration.
- Real `syft`/`grype`/`semgrep` binaries in a CI/Docker image (the app already detects and
  prefers them via `tool_available()` — only the fallback path is exercised in this build).
- Per-repository ephemeral Docker sandboxes to run real `npm test` / `pytest` for the QA agent,
  replacing the labeled simulation.
- Authentication + role-based access control (the approval/audit models already carry a
  `decided_by` field to build on).
- A real GitHub PR-creation path gated behind an explicit, separately-confirmed user action —
  distinct from the always-safe DEMO PR preparation this build ships with.
- Postgres + Redis-backed task queue for multi-repository concurrent scanning at scale.
