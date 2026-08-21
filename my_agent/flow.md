# CareerOS — ArmorIQ Governed Multi-Agent Pipeline Flow

## Overview

CareerOS is an automated multi-agent platform governed by **ArmorIQ Security SDK**. The Root Coordinator agent plans the workflow and cryptographically delegates authority to 5 specialized sub-agents. Each sub-agent operates with its own **cryptographic keypair**, connects to its own **dedicated MCP server**, and executes actions using `invoke()`.

---

## ArmorIQ Governed Pipeline Diagram

```
                             User uploads resume
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │    root_coordinator_agent     │
                      │  (Root Identity / Keypair 0)  │
                      └───────────────┬───────────────┘
                                      │
                         ArmorIQ capture_plan()
                         ArmorIQ delegate()
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │ (Token 1: resumes:write)   │ (Token 2: analysis:write)  │ (Token 3: profiles:write)
         ▼                            ▼                            ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│ resume_extractor │         │ resume_analyzer  │         │  profile_maker   │
│   (Keypair 1)    │         │   (Keypair 2)    │         │   (Keypair 3)    │
└────────┬─────────┘         └────────┬─────────┘         └────────┬─────────┘
         │                            │                            │
  invoke()                    invoke()                    invoke()
         ▼                            ▼                            ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  MCP Extractor   │         │   MCP Analyzer   │         │   MCP Profiler   │
│      Server      │         │      Server      │         │      Server      │
└──────────────────┘         └──────────────────┘         └──────────────────┘
         │ (Token 4: search:write)    │ (Token 5: rank:write)
         ▼                            ▼
┌──────────────────┐         ┌──────────────────┐
│opportunity_scout │         │opportunity_ranker│
│   (Keypair 4)    │         │   (Keypair 5)    │
└────────┬─────────┘         └────────┬─────────┘
         │                            │
  invoke()                    invoke()
         ▼                            ▼
┌──────────────────┐         ┌──────────────────┐
│    MCP Scout     │         │    MCP Ranker    │
│      Server      │         │      Server      │
└──────────────────┘         └──────────────────┘
         │
         │ ⚡ DEMO ATTACK / SCOPE VIOLATION
         ▼
  Attempt: auto_apply_job()
  ArmorIQ Check: NOT IN DELEGATED SCOPE
  Result: 🛑 BLOCKED Cryptographically & Logged in Dashboard
```

---

## 1. ArmorIQ SDK Call Sequence

### Step 1: Plan Capture (`capture_plan`)
The Root Coordinator registers the execution plan with ArmorIQ before pipeline execution:
```python
from armoriq import ArmorIQClient

armoriq = ArmorIQClient(api_key=os.getenv("ARMORIQ_API_KEY"))

plan = armoriq.capture_plan(
    agent_id="root_coordinator_agent",
    intent="Execute CareerOS pipeline: extract, analyze, profile, scout, rank opportunities",
    allowed_tools=[
        "mcp_extractor.extract_and_store_resume",
        "mcp_analyzer.analyze_and_store_resume",
        "mcp_profiler.build_and_store_profile",
        "mcp_scout.scout_and_store_opportunities",
        "mcp_ranker.rank_and_store_opportunities",
    ]
)
```

### Step 2: Cryptographic Delegation (`delegate`)
Root Agent delegates scoped authority to sub-agent keypairs:
```python
# Delegate authority to opportunity_scout
scout_delegation = armoriq.delegate(
    parent_agent_id="root_coordinator_agent",
    sub_agent_id="opportunity_scout",
    sub_agent_keypair=scout_keypair,
    allowed_scopes=["profiles:read", "opportunities:write", "web:search"],
    allowed_tools=["mcp_scout.scout_and_store_opportunities"],
    ttl_seconds=300  # Token expires in 5 minutes
)
```

### Step 3: Tool Invocation (`invoke`)
Sub-agent executes tool using its delegation token and keypair:
```python
result = armoriq.invoke(
    sub_agent_id="opportunity_scout",
    sub_agent_keypair=scout_keypair,
    delegation_token=scout_delegation.token,
    tool_name="mcp_scout.scout_and_store_opportunities",
    tool_args={"profile_id": 1, "keywords": ["Python developer"]}
)
```

---

## 2. Sub-Agent & Dedicated MCP Server Specifications

### Stage 1: `resume_extractor`
- **Identity:** `keypair_extractor.pem` (Ed25519)
- **MCP Server:** `mcp_extractor_server` (Port 8001 / Stdio)
- **Tool:** `mcp_extractor.extract_and_store_resume(resume_text: str)`
- **Delegated Scope:** `resumes:write`
- **Behavior:** Parses raw resume text into structured fields (name, email, phone, education, experience, skills, projects) and writes to `resumes` table.

### Stage 2: `resume_analyzer`
- **Identity:** `keypair_analyzer.pem` (Ed25519)
- **MCP Server:** `mcp_analyzer_server` (Port 8002 / Stdio)
- **Tool:** `mcp_analyzer.analyze_and_store_resume(resume_id: int)`
- **Delegated Scope:** `resumes:read`, `analysis:write`
- **Behavior:** Reads resume record from DB, identifies strengths/weaknesses/experience level/domain focus, and writes to `resume_analysis` table.

### Stage 3: `profile_maker`
- **Identity:** `keypair_profiler.pem` (Ed25519)
- **MCP Server:** `mcp_profiler_server` (Port 8003 / Stdio)
- **Tool:** `mcp_profiler.build_and_store_profile(resume_id: int)`
- **Delegated Scope:** `analysis:read`, `profiles:write`
- **Behavior:** Combines resume and analysis data into a candidate profile (tech stack, interests, career goals, search keywords) and writes to `profiles` table.

### Stage 4: `opportunity_scout`
- **Identity:** `keypair_scout.pem` (Ed25519)
- **MCP Server:** `mcp_scout_server` (Port 8004 / Stdio)
- **Tool:** `mcp_scout.scout_and_store_opportunities(profile_id: int)`
- **Delegated Scope:** `profiles:read`, `opportunities:write`, `web:search`
- **Behavior:** Reads profile keywords, queries search APIs across jobs, internships, competitions, and conclaves, and writes to `opportunities` table.

### Stage 5: `opportunity_ranker`
- **Identity:** `keypair_ranker.pem` (Ed25519)
- **MCP Server:** `mcp_ranker_server` (Port 8005 / Stdio)
- **Tool:** `mcp_ranker.rank_and_store_opportunities(profile_id: int)`
- **Delegated Scope:** `opportunities:read`, `ranked:write`
- **Behavior:** Reads candidate profile and raw opportunities, scores them (0-100), and writes to `ranked_opportunities` table.

---

## 3. Demo Scope Violation (ArmorIQ Block Verification)

To prove compliance with Hackathon Rule #3 ("Demo at least one scope violation"):

```python
# DEMO: Poisoned Prompt / Scope Escalation Attack
try:
    # opportunity_scout attempts an unauthorized action (auto-apply / payments)
    armoriq.invoke(
        sub_agent_id="opportunity_scout",
        sub_agent_keypair=scout_keypair,
        delegation_token=scout_delegation.token,
        tool_name="mcp_scout.auto_apply_job",  # NOT in delegated scope!
        tool_args={"job_id": 42, "credit_card_id": 999}
    )
except ArmorIQScopeViolationError as e:
    print("🛡️ ArmorIQ Block Success! Scope violation caught:")
    print(f"   Reason: {e.message}")
    print(f"   Delegation Chain: {e.delegation_chain}")
```

**Expected ArmorIQ Log Output:**
```json
{
  "event": "SCOPE_VIOLATION_BLOCKED",
  "parent_agent": "root_coordinator_agent",
  "sub_agent": "opportunity_scout",
  "requested_tool": "mcp_scout.auto_apply_job",
  "allowed_tools": ["mcp_scout.scout_and_store_opportunities"],
  "status": "BLOCKED",
  "timestamp": "2026-08-21T10:55:00Z"
}
```

---

## 4. SQLite Database Schema (`career_os.db`)

All tables maintain foreign key integrity across stages:

```sql
CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, email TEXT, phone TEXT,
    education TEXT, experience TEXT, skills TEXT,
    projects TEXT, certifications TEXT, raw_text TEXT,
    created_at TEXT
);

CREATE TABLE resume_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id INTEGER REFERENCES resumes(id),
    strengths TEXT, weaknesses TEXT, experience_level TEXT,
    domain_focus TEXT, key_technologies TEXT, summary TEXT,
    created_at TEXT
);

CREATE TABLE profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id INTEGER REFERENCES resumes(id),
    tech_stack TEXT, interests TEXT, career_goals TEXT,
    preferred_roles TEXT, experience_summary TEXT,
    search_keywords TEXT, created_at TEXT
);

CREATE TABLE opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER REFERENCES profiles(id),
    title TEXT, url TEXT, description TEXT, source TEXT,
    category TEXT, deadline TEXT, created_at TEXT
);

CREATE TABLE ranked_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER REFERENCES opportunities(id),
    profile_id INTEGER REFERENCES profiles(id),
    relevance_score INTEGER, match_reasons TEXT, rank INTEGER,
    category TEXT, created_at TEXT
);
```

---

## 5. Summary of Hackathon Guarantees

1. **Explicit Delegation Chain:** Root -> Sub-Agent with cryptographically signed tokens.
2. **Keypair per Sub-Agent:** Independent client keypairs prevent identity impersonation.
3. **Decoupled MCP Tool Servers:** Each sub-agent invokes dedicated MCP tools via `invoke()`.
4. **Verifiable Block Enforcement:** Out-of-scope actions fail cryptographically.
5. **Dashboard Auditing:** Full receipt trail of allowed vs blocked execution.
