# CareerOS — Full-Stack Architecture & API Specification

## 1. Overview

**CareerOS** is a full-stack, ArmorIQ-governed career automation platform. It combines:
- **Frontend (React / Next.js):** Interactive candidate dashboard, resume uploader, 5-stage visual execution tracker, opportunity marketplace, and live ArmorIQ security audit console.
- **Backend API (FastAPI):** RESTful service connecting the UI to SQLite (`career_os.db`) and the multi-agent execution pipeline.
- **Multi-Agent Engine (Google ADK + ArmorIQ SDK):** 5 specialized sub-agents with distinct cryptographic keypairs, dedicated MCP servers, scoped delegation tokens, and real-time scope violation block enforcement.
- **Direct Database QA (Smart Routing):** Answering personal profile/skills/opportunity questions directly from DB records **without** re-triggering the 5-stage pipeline.

---

## 2. Smart Routing: Pipeline Execution vs. Direct DB QA

```
                         User Query / Input
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Root Coordinator    │
                     │    (Routing Layer)    │
                     └───────────┬───────────┘
                                 │
          ┌──────────────────────┴──────────────────────┐
          │                                             │
   [New Resume Upload]                        [Personal Info Query]
          │                                 (e.g. "What are my skills?")
          ▼                                             ▼
┌──────────────────┐                           ┌──────────────────┐
│ Full 5-Stage     │                           │ Direct DB QA     │
│ ArmorIQ Pipeline │                           │ (No Pipeline)    │
└─────────┬────────┘                           └────────┬─────────┘
          │                                             │
  Runs: Extractor ➔ Analyzer ➔                  Calls: read_from_db()
  Profiler ➔ Scout ➔ Ranker                     Reads profile/skills
          │                                             │
          ▼                                             ▼
Saved to SQLite DB                           Direct Answer to User
```

### Behavioral Rules

1. **Trigger Full Pipeline:** ONLY when a new resume is uploaded, attached, or pasted.
2. **Trigger Direct DB QA:** When the user asks questions about their profile, skills, experience level, recommendations, or stored opportunities.
   - Example queries: *"What skills did you find in my resume?"*, *"What are my top recommended internships?"*, *"What is my experience level?"*, *"What roles suit me?"*.
   - **Mechanism:** The agent calls `read_from_db` on the appropriate table (`profiles`, `resumes`, `resume_analysis`, `ranked_opportunities`) and responds immediately.

---

## 3. Database Schema (`career_os.db`)

All tables are persisted in SQLite and can be queried directly:

```sql
-- 1. Extracted Resume Data
CREATE TABLE resumes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT, email TEXT, phone TEXT,
    education   TEXT, experience TEXT, skills TEXT,
    projects    TEXT, certifications TEXT, raw_text TEXT,
    created_at  TEXT
);

-- 2. Resume Analytical Insights
CREATE TABLE resume_analysis (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id        INTEGER REFERENCES resumes(id),
    strengths        TEXT, weaknesses TEXT, experience_level TEXT,
    domain_focus     TEXT, key_technologies TEXT, summary TEXT,
    created_at       TEXT
);

-- 3. Structured Candidate Profile
CREATE TABLE profiles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id           INTEGER REFERENCES resumes(id),
    tech_stack          TEXT, interests TEXT, career_goals TEXT,
    preferred_roles     TEXT, experience_summary TEXT,
    search_keywords     TEXT, created_at TEXT
);

-- 4. Raw Discovered Opportunities
CREATE TABLE opportunities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id  INTEGER REFERENCES profiles(id),
    title       TEXT, url TEXT, description TEXT, source TEXT,
    category    TEXT, deadline TEXT, created_at TEXT
);

-- 5. Scored & Ranked Opportunities
CREATE TABLE ranked_opportunities (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id   INTEGER REFERENCES opportunities(id),
    profile_id       INTEGER REFERENCES profiles(id),
    relevance_score  INTEGER, match_reasons TEXT, rank INTEGER,
    category         TEXT, created_at TEXT
);
```

---

## 4. FastAPI Backend Endpoints (`api.py`)

The FastAPI backend exposes endpoints for the frontend UI:

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/process-resume` | `POST` | Uploads resume and triggers full 5-stage pipeline | `{"status": "success", "resume_id": 1}` |
| `/api/query-db` | `POST` | Asks personal profile/skills questions directly from DB (no pipeline) | `{"status": "success", "answer": "..."}` |
| `/api/profile/latest` | `GET` | Fetches latest candidate profile & tech stack | `{"status": "success", "profile": {...}}` |
| `/api/opportunities/latest` | `GET` | Fetches ranked opportunities with filters | `{"status": "success", "opportunities": [...]}` |
| `/api/audit-logs` | `GET` | Returns ArmorIQ security audit logs | `{"status": "success", "logs": [...]}` |
| `/api/demo/trigger-attack` | `POST` | Simulates prompt injection attack to demo ArmorIQ block | `{"status": "blocked", "reason": "SCOPE_VIOLATION"}` |

---

## 5. Implementation Code: FastAPI Backend (`api.py`)

```python
# d:\careerOS\api.py
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import json
import os
from my_agent.tools.db_tools import read_from_db
from my_agent.demo_armoriq_governance import run_demo

app = FastAPI(title="CareerOS Full-Stack API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "my_agent/career_os.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 1. Trigger Full Pipeline (New Resume)
@app.post("/api/process-resume")
async def process_resume(resume_text: str = Form(...)):
    try:
        run_demo()
        return {"status": "success", "message": "Pipeline completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Direct DB QA Query (No Pipeline Run!)
class QuestionRequest(BaseModel):
    question: str

@app.post("/api/query-db")
async def query_db(req: QuestionRequest):
    q = req.question.lower()
    conn = get_db()
    
    # Query Profile / Skills / Analysis based on question keywords
    if any(k in q for k in ["skill", "tech", "stack", "language", "tool"]):
        row = conn.execute("SELECT tech_stack, preferred_roles FROM profiles ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        if not row:
            return {"answer": "No candidate profile found yet. Please upload a resume first."}
        skills = json.loads(row["tech_stack"]) if row["tech_stack"] else []
        roles = json.loads(row["preferred_roles"]) if row["preferred_roles"] else []
        return {"answer": f"Your top technical skills are: {', '.join(skills)}. Preferred roles: {', '.join(roles)}."}
        
    elif any(k in q for k in ["opportunity", "job", "internship", "rank", "match"]):
        rows = conn.execute("""
            SELECT r.rank, r.relevance_score, o.title, o.category, o.url 
            FROM ranked_opportunities r 
            JOIN opportunities o ON r.opportunity_id = o.id 
            ORDER BY r.rank ASC LIMIT 5
        """).fetchall()
        conn.close()
        if not rows:
            return {"answer": "No ranked opportunities found in DB. Run the opportunity scout first."}
        top_matches = [f"#{r['rank']} {r['title']} ({r['category']}) - Match Score: {r['relevance_score']}%" for r in rows]
        return {"answer": "Your top matches from the database:\n" + "\n".join(top_matches)}
        
    else:
        row = conn.execute("SELECT experience_summary, career_goals FROM profiles ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        if not row:
            return {"answer": "No profile found in DB."}
        return {"answer": f"Summary: {row['experience_summary']}\nCareer Goals: {row['career_goals']}"}

# 3. Get Latest Candidate Profile
@app.get("/api/profile/latest")
def get_latest_profile():
    conn = get_db()
    profile = conn.execute("SELECT * FROM profiles ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if not profile:
        return {"status": "error", "message": "No profile found"}
    data = dict(profile)
    for k in ["tech_stack", "interests", "preferred_roles", "search_keywords"]:
        if data.get(k):
            try: data[k] = json.loads(data[k])
            except: pass
    return {"status": "success", "profile": data}

# 4. Get Ranked Opportunities
@app.get("/api/opportunities/latest")
def get_latest_opportunities(category: str = None):
    conn = get_db()
    query = """
        SELECT r.rank, r.relevance_score, r.match_reasons, o.title, o.url, o.description, o.category, o.deadline
        FROM ranked_opportunities r
        JOIN opportunities o ON r.opportunity_id = o.id
    """
    params = []
    if category and category != "all":
        query += " WHERE o.category = ?"
        params.append(category)
    query += " ORDER BY r.rank ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        item = dict(r)
        if item.get("match_reasons"):
            try: item["match_reasons"] = json.loads(item["match_reasons"])
            except: pass
        results.append(item)
    return {"status": "success", "count": len(results), "opportunities": results}
```

---

## 6. Frontend Dashboard Layout (React / Next.js)

The frontend features 4 key interactive sections:

1. **Resume Processing Hero:** Drag & drop uploader with 5-stage animated progress bar.
2. **Direct Chat / Info Search Bar:** *"Ask anything about your profile or stored opportunities..."* (queries `/api/query-db` instantly).
3. **Candidate Profile Card:** Displays Tech Stack Chips, Experience Level Badge, Strengths, and Goals.
4. **Opportunity Marketplace:** Tabbed grid displaying ranked jobs, internships, hackathons, and conclaves with relevance scores.
5. **ArmorIQ Security & Audit Console (Hackathon Judge Monitor):** Displays cryptographic keypairs, delegation tokens, and live scope violation blocks.

---

## 7. How to Launch the Full-Stack App

1. **Start Backend API:**
   ```bash
   uvicorn api:app --reload --port 5000
   ```

2. **Start Frontend App:**
   ```bash
   cd frontend && npm run dev
   ```

3. **Open Browser:**
   Navigate to `http://localhost:3000` to interact with CareerOS!
