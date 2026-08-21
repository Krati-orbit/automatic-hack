# CareerOS — Hackathon Submission & Live Demo Guide

> **Hackathon Track:** Problem 2 — "Who authorized that?" (Multi-Agent Delegation & Governance)  
> **Core Engine:** ArmorIQ SDK + Google ADK + 5 Isolated MCP Tool Servers + SQLite  
> **GitHub Repository:** [https://github.com/Krati-orbit/automatic-hack](https://github.com/Krati-orbit/automatic-hack)

---

## 1. Executive Summary for Submission

**CareerOS** is a zero-trust multi-agent career automation platform. It processes candidate resumes, builds structured candidate profiles, discovers real-world opportunities (jobs, internships, hackathons, conclaves), and ranks them by relevance.

To solve **Problem 2 ("Who authorized that?")**, CareerOS implements **Zero-Trust Cryptographic Delegation**:
- **Keypair Isolation:** 5 sub-agents run with independent RSA/Ed25519 keypairs (`resume_extractor`, `resume_analyzer`, `profile_maker`, `opportunity_scout`, `opportunity_ranker`).
- **Decoupled MCP Tool Servers:** Each sub-agent invokes dedicated tools via its own isolated MCP server (`mcp_extractor_server`, `mcp_analyzer_server`, `mcp_profiler_server`, `mcp_scout_server`, `mcp_ranker_server`).
- **ArmorIQ SDK Core Methods:** Uses `capture_plan()` on Root Coordinator, `delegate()` for signed delegation tokens (with 300s TTL), and `invoke()` for tool execution.
- **Cryptographic Scope Interception:** Any out-of-scope tool invocation (e.g. `opportunity_scout` attempting `auto_apply_job`) is cryptographically intercepted and **blocked before execution**.

---

## 2. Architecture & Real MCP Pipeline

```
  Candidate Resume (PDF / Text)
                │
                ▼
   ┌──────────────────────────┐
   │  Root Coordinator Agent  │ ──► capture_plan() & delegate(token)
   └────────────┬─────────────┘
                │
 ┌──────────────┼──────────────┬──────────────┬──────────────┐
 ▼              ▼              ▼              ▼              ▼
Keypair 1      Keypair 2      Keypair 3      Keypair 4      Keypair 5
Sub-Agent 1    Sub-Agent 2    Sub-Agent 3    Sub-Agent 4    Sub-Agent 5
Extractor      Analyzer       Profiler       Scout          Ranker
 │              │              │              │              │
 ▼              ▼              ▼              ▼              ▼
MCP Server 1   MCP Server 2   MCP Server 3   MCP Server 4   MCP Server 5
(resumes:write)(analysis:write)(profiles:write)(opportunities:w)(ranked:write)
```

### Real Execution Flow:
1. **`mcp_extractor_server`**: Parses resume text/PDF into `resumes` table (`resume_id`).
2. **`mcp_analyzer_server`**: Analyzes technical strengths, weaknesses, and experience level into `resume_analysis` table.
3. **`mcp_profiler_server`**: Generates a dedicated Candidate Profile in `profiles` table (`profile_id`).
4. **`mcp_scout_server`**: Runs **real web search** (via Firecrawl MCP / DuckDuckGo fallback) discovering real live opportunities.
5. **`mcp_ranker_server`**: Scores opportunities 0-100% against candidate skills and stores ranked matches in `ranked_opportunities` table.

---

## 3. How to Run the App Local Servers

### Step 1: Start Backend API & ArmorIQ Server
```bash
python -m uvicorn api:app --reload --port 8000
```
*(Runs on `http://127.0.0.1:8000`)*

### Step 2: Start Frontend Dashboard
```bash
cd frontend
npm run dev
```
*(Runs on `http://localhost:5173`)*

### Step 3: Start Google ADK Web UI (Optional ADK Agent Dev UI)
```bash
adk web --port 8080 my_agent
```
*(Runs on `http://127.0.0.1:8080`)*

---

## 4. Live Demo Script for Video Recording (2-3 Minutes)

### **Part 1: 5-Stage Governed Pipeline Demo (0:00 - 1:00)**
1. Open `http://localhost:5173`.
2. Click **Upload PDF Resume** or paste resume text into the box.
3. Click **Process & Create Candidate Profile**.
4. Show the **5-Stage Visual Stepper** executing in real-time (~1.18 seconds).
5. Switch to **👤 Candidate Profile** tab to show the extracted Tech Stack badges, AI Evaluation Report (Strengths & Growth areas), and Executive Summary.
6. Switch to **🎯 Opportunities** tab to show real scouted jobs/internships ranked by relevance score (e.g. 95% Match).

### **Part 2: ArmorIQ Scope Attack & Trajectory Trace Demo (1:00 - 2:15)**
1. In the top header bar, ensure **ArmorIQ Shield: ON** (Green).
2. Click **Simulate Prompt Attack**.
3. **Show Protection Result**: Green/Cyan banner appears:  
   `🛡️ ARMORIQ PROTECTED & BLOCKED BEFORE EXECUTION`  
   Highlight the **Trajectory Trace Graph**:
   - *Step 1:* Root Coordinator issued signed delegation token for `['mcp_scout.scout_and_store_opportunities']`.
   - *Step 2:* Sub-agent `opportunity_scout` received scope.
   - *Step 3:* Prompt injection payload requested unauthorized tool `auto_apply_job`.
   - *Step 4:* **ArmorIQ Interceptor caught violation and BLOCKED execution before damage occurred!**
4. Toggle **ArmorIQ Shield: OFF** (Red).
5. Click **Simulate Prompt Attack** again.
6. **Show Security Breach Simulation**: Red banner appears:  
   `🛑 UNSECURED SCOPE BREACH EXPLOITED (SHIELD WAS OFF)`  
   Demonstrates what happens in an ungoverned system when ArmorIQ protection is absent.

### **Part 3: Interactive Candidate Chat & SQLite Audit Logs (2:15 - 3:00)**
1. Switch to **💬 AI Assistant Chat** tab.
2. Ask: *"What are my top technical skills?"* or click quick prompt chip. Show response read directly from SQLite for that profile.
3. Show live **ArmorIQ Governance Monitor Audit Logs** table displaying cryptographic token IDs and event statuses.

---

## 5. Submission Checklist

- [x] **GitHub Repo:** `https://github.com/Krati-orbit/automatic-hack`
- [x] **Core Methods:** `capture_plan()`, `delegate()`, `invoke()` integrated in `armoriq_wrapper.py`
- [x] **Keypair Isolation:** 5 sub-agent RSA keypairs generated in `armoriq_crypto.py`
- [x] **MCP Tool Isolation:** 5 decoupled MCP server scripts in `my_agent/mcp_servers/`
- [x] **Scope Attack Demo:** `auto_apply_job` interception & Trajectory Trace Graph
- [x] **Persistence:** Real SQLite database storage (`career_os.db`)
