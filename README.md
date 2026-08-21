# 🤖 CareerOS — Zero-Trust Multi-Agent Career Automation Platform

> **Hackathon Submission Track:** Problem 2 — *"Who authorized that?"* (Multi-Agent Delegation & Governance)  
> **Core Architecture:** ArmorIQ SDK + Google ADK + 5 Decoupled MCP Tool Servers + SQLite  
> **GitHub Repository:** [https://github.com/Krati-orbit/automatic-hack](https://github.com/Krati-orbit/automatic-hack)

---

## 🌟 Executive Summary

**CareerOS** is a zero-trust multi-agent career automation platform that processes candidate resumes, builds rich relational profiles, scouts real live internet opportunities (jobs, internships, hackathons, competitions, conclaves), and ranks them by 0-100% relevance score.

To solve **Problem 2 ("Who authorized that?")**, CareerOS implements **Zero-Trust Cryptographic Delegation Protocols**:
* **RSA Keypair Isolation:** 5 sub-agents run with independent RSA asymmetric keypairs (`resume_extractor`, `resume_analyzer`, `profile_maker`, `opportunity_scout`, `opportunity_ranker`).
* **Decoupled MCP Tool Servers:** Each sub-agent invokes tools strictly through its own isolated MCP tool server module (`my_agent/mcp_servers/`).
* **ArmorIQ Core Security Methods:** Uses `capture_plan()` on Root Coordinator, `delegate()` for signed delegation tokens (with 300-second TTL), and `invoke()` for cryptographic tool verification.
* **Real-Time Scope Interception:** Any out-of-scope tool call (e.g. a prompt injection forcing `opportunity_scout` to call `auto_apply_job`) is cryptographically caught and **blocked before execution**.

---

## ✨ Key Features

* **⚡ 5-Stage Governed Pipeline:** Automated workflow taking raw resume text or PDF uploads through Extraction $\rightarrow$ Analysis $\rightarrow$ Profiling $\rightarrow$ Scouting $\rightarrow$ Ranking.
* **🛡️ ArmorIQ Shield Toggle & Attack Visualizer:** Interactive UI to switch between **ArmorIQ Shield: ON** (intercepts & blocks prompt attacks with 4-step trajectory traces) and **ArmorIQ Shield: OFF** (demonstrates unsecured scope breaches).
* **🎯 Live Opportunity Scouting:** Real-world web search powered by Firecrawl MCP discovering live opportunities across 5 distinct categories.
* **👤 Rich Candidate Profile Library:** Extracts and presents complete candidate details: Education, Work History, Portfolio Projects, Certifications, and Relational Technical Stack.
* **💬 AI Assistant Chat (Direct DB QA):** Direct SQL-backed candidate assistant answering queries about skills, target roles, and top-ranked matches.
* **🗄️ Relational SQLite Persistence:** All candidates, resumes, profiles, and ranked opportunities are stored permanently in `career_os.db`.

---

## 🏛️ System Architecture & Sub-Agent Breakdown

```text
                  Candidate Resume (PDF / Text Input)
                                  │
                                  ▼
                   ┌────────────────────────────┐
                   │   Root Coordinator Agent   │ ──► capture_plan() & delegate(tokens)
                   └──────────────┬─────────────┘
                                  │ (Signed 300s TTL Delegation Tokens)
  ┌───────────────────┬───────────┴───────────┬───────────────────┐
  ▼                   ▼                       ▼                   ▼
Sub-Agent 1        Sub-Agent 2             Sub-Agent 3         Sub-Agent 4         Sub-Agent 5
resume_extractor   resume_analyzer         profile_maker       opportunity_scout   opportunity_ranker
(Keypair 1)        (Keypair 2)             (Keypair 3)         (Keypair 4)         (Keypair 5)
  │                   │                       │                   │                   │
  ▼                   ▼                       ▼                   ▼                   ▼
MCP Server 1       MCP Server 2            MCP Server 3        MCP Server 4        MCP Server 5
(resumes:write)    (analysis:write)        (profiles:write)    (opportunities:w)   (ranked:write)
```

| Sub-Agent Identity | Keypair | Delegated Scope | Dedicated MCP Server | Core Responsibility |
| :--- | :---: | :--- | :--- | :--- |
| **`resume_extractor`** | RSA Keypair 1 | `resumes:write` | `mcp_extractor_server` | Parses candidate contact info, education, experience, and skills into `resumes` table. |
| **`resume_analyzer`** | RSA Keypair 2 | `analysis:write` | `mcp_analyzer_server` | Evaluates technical strengths, growth areas, and domain focus into `resume_analysis` table. |
| **`profile_maker`** | RSA Keypair 3 | `profiles:write` | `mcp_profiler_server` | Constructs technical stack, target roles, career goals, and executive summary into `profiles` table. |
| **`opportunity_scout`** | RSA Keypair 4 | `opportunities:write` | `mcp_scout_server` | Searches live internet via Firecrawl MCP across Jobs, Internships, Competitions, Hackathons, Conclaves. |
| **`opportunity_ranker`** | RSA Keypair 5 | `ranked:write` | `mcp_ranker_server` | Scores matches 0-100% against candidate profile and saves ranked results into `ranked_opportunities` table. |

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend UI** | React 19, Vite 8, Lucide React, Glassmorphic Vanilla CSS, Tailwind CSS v4 |
| **Backend REST API** | FastAPI v2.0 (Python 3.13), Uvicorn ASGI, `pypdf` PDF Extraction Engine |
| **Multi-Agent Engine** | Google ADK (`google.adk.agents.llm_agent.Agent`), 5 Decoupled MCP Tool Servers |
| **Zero-Trust Governance** | ArmorIQ SDK Protocol (`capture_plan`, `delegate`, `invoke`), Cryptographic RSA Keypairs |
| **AI Inference & Search** | LiteLLM, Groq Cloud LLM API (`groq/openai/gpt-oss-20b`), Firecrawl MCP Web Search |
| **Database & Storage** | SQLite 3 (`career_os.db`) storing 5 relational candidate tables |

---

## 🚀 Installation & Running Guide

### **Prerequisites**
* Python 3.10+
* Node.js 18+
* Groq Cloud API Key (or set in `.env`)

---

### **Step 1: Environment Setup**
Create a `.env` file in the project root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=groq/openai/gpt-oss-20b
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

---

### **Step 2: Run Backend API Server (FastAPI)**
In your main terminal (`d:\careerOS`):

```powershell
python -m uvicorn api:app --reload --port 8000
```
* **Backend API Base:** [http://localhost:8000](http://localhost:8000)
* **Swagger API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### **Step 3: Run Frontend Dashboard (React + Vite)**
Open a second terminal window:

```powershell
cd frontend
npm run dev
```
* **Frontend Web App:** [http://localhost:5173](http://localhost:5173)

---

### **Step 4: Run Google ADK Web UI (Optional Dev Interface)**
Open a third terminal window:

```powershell
adk web --port 8080 my_agent
```
* **Google ADK Dashboard:** [http://localhost:8080](http://localhost:8080)

---

## 🧪 ArmorIQ Security & Attack Interception Demo

1. Open [http://localhost:5173](http://localhost:5173).
2. **Shield ON (Protected Mode)**:
   * Ensure **ArmorIQ Shield** toggle in top header is **ON (Green)**.
   * Click **Simulate Prompt Attack**.
   * **Result:** ArmorIQ intercepts the unauthorized call `auto_apply_job` and displays a green banner `🛡️ ARMORIQ PROTECTED & BLOCKED BEFORE EXECUTION` with a 4-step Trajectory Trace Graph.
3. **Shield OFF (Unsecured Bypass)**:
   * Toggle **ArmorIQ Shield** to **OFF (Red)**.
   * Click **Simulate Prompt Attack**.
   * **Result:** Bypasses governance checks and displays `🛑 UNSECURED SCOPE BREACH EXPLOITED`, demonstrating what happens in ungoverned systems.

---

## 📡 REST API Endpoints Summary

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/process-resume` | `POST` | Triggers full 5-stage ArmorIQ governed pipeline on resume text. |
| `/api/upload-resume-pdf` | `POST` | Extracts text from uploaded PDF file and runs 5-stage pipeline. |
| `/api/profiles` | `GET` | Lists all candidate profiles in SQLite. |
| `/api/profiles/{profile_id}` | `GET` | Fetches complete relational candidate payload (profile, resume, analysis, opportunities). |
| `/api/resumes` | `GET` | Lists all parsed resumes in SQLite. |
| `/api/profiles/{profile_id}/opportunities` | `GET` | Fetches opportunities ranked for candidate profile. |
| `/api/query-db` | `POST` | Direct DB QA queries for candidate AI Assistant Chat. |
| `/api/audit-logs` | `GET` | Fetches live ArmorIQ governance audit trail logs. |
| `/api/demo/trigger-attack` | `POST` | Simulates prompt attack with ArmorIQ Shield ON/OFF toggle. |

---

## 📜 License & Acknowledgments

* **Hackathon Submission Track:** Problem 2 — *"Who authorized that?"*
* **Core Technologies:** ArmorIQ SDK, Google Agent Development Kit (ADK), LiteLLM, Groq Cloud AI, FastAPI, React.
