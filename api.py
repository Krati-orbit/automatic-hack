"""FastAPI Backend Server for CareerOS.

Exposes REST API endpoints for:
- /api/process-resume: Triggers the ArmorIQ governed 5-stage pipeline
- /api/query-db: Direct DB QA queries (answering profile/skills queries without pipeline)
- /api/profile/latest: Fetches current candidate profile & tech stack
- /api/opportunities/latest: Fetches ranked opportunities with category filters
- /api/audit-logs: Fetches live ArmorIQ governance audit trail logs
- /api/demo/trigger-attack: Simulates prompt injection attack to demo scope violation block
"""

import json
import os
import sqlite3
import sys
from typing import Optional

from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from my_agent.armoriq_crypto import generate_pipeline_keypairs
from my_agent.armoriq_wrapper import ArmorIQClient, ArmorIQScopeViolationError
from my_agent.mcp_servers.mcp_extractor_server import extract_and_store_resume
from my_agent.mcp_servers.mcp_analyzer_server import analyze_and_store_resume
from my_agent.mcp_servers.mcp_profiler_server import build_and_store_profile
from my_agent.mcp_servers.mcp_scout_server import scout_and_store_opportunities, auto_apply_job
from my_agent.mcp_servers.mcp_ranker_server import rank_and_store_opportunities

app = FastAPI(title="CareerOS API Server", version="1.0")

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_agent", "career_os.db")
global_armoriq = ArmorIQClient()
global_keypairs = generate_pipeline_keypairs()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class QueryRequest(BaseModel):
    question: str


# ── Root Welcome Endpoint ───────────────────────────────────────────────────
@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "CareerOS ArmorIQ Governed API Server",
        "version": "1.0",
        "documentation": "/docs",
        "endpoints": {
            "process_resume": "/api/process-resume (POST)",
            "query_db": "/api/query-db (POST)",
            "latest_profile": "/api/profile/latest (GET)",
            "latest_opportunities": "/api/opportunities/latest (GET)",
            "audit_logs": "/api/audit-logs (GET)",
            "trigger_attack": "/api/demo/trigger-attack (POST)"
        }
    }


# ── 1. Process Resume Endpoint (Full Pipeline) ──────────────────────────────
@app.post("/api/process-resume")
async def process_resume(resume_text: str = Form(...)):
    """Executes the 5-stage governed pipeline with ArmorIQ SDK."""
    try:
        root_kp = global_keypairs["root_coordinator_agent"]
        plan = global_armoriq.capture_plan(
            agent_id="root_coordinator_agent",
            intent="Parse candidate resume, build profile, discover opportunities, rank matches",
            allowed_tools=[
                "mcp_extractor.extract_and_store_resume",
                "mcp_analyzer.analyze_and_store_resume",
                "mcp_profiler.build_and_store_profile",
                "mcp_scout.scout_and_store_opportunities",
                "mcp_ranker.rank_and_store_opportunities",
            ]
        )

        # Issue delegation tokens
        tok_extractor = global_armoriq.delegate("root_coordinator_agent", root_kp, "resume_extractor", ["resumes:write"], ["mcp_extractor.extract_and_store_resume"], 300)
        tok_analyzer = global_armoriq.delegate("root_coordinator_agent", root_kp, "resume_analyzer", ["resumes:read", "analysis:write"], ["mcp_analyzer.analyze_and_store_resume"], 300)
        tok_profiler = global_armoriq.delegate("root_coordinator_agent", root_kp, "profile_maker", ["analysis:read", "profiles:write"], ["mcp_profiler.build_and_store_profile"], 300)
        tok_scout = global_armoriq.delegate("root_coordinator_agent", root_kp, "opportunity_scout", ["profiles:read", "opportunities:write", "web:search"], ["mcp_scout.scout_and_store_opportunities"], 300)
        tok_ranker = global_armoriq.delegate("root_coordinator_agent", root_kp, "opportunity_ranker", ["opportunities:read", "ranked:write"], ["mcp_ranker.rank_and_store_opportunities"], 300)

        # Execute 5 stages
        res_1 = global_armoriq.invoke("resume_extractor", global_keypairs["resume_extractor"], tok_extractor, root_kp, "mcp_extractor.extract_and_store_resume", {"resume_text": resume_text}, extract_and_store_resume)
        resume_id = res_1.get("resume_id")

        res_2 = global_armoriq.invoke("resume_analyzer", global_keypairs["resume_analyzer"], tok_analyzer, root_kp, "mcp_analyzer.analyze_and_store_resume", {"resume_id": resume_id}, analyze_and_store_resume)

        res_3 = global_armoriq.invoke("profile_maker", global_keypairs["profile_maker"], tok_profiler, root_kp, "mcp_profiler.build_and_store_profile", {"resume_id": resume_id}, build_and_store_profile)
        profile_id = res_3.get("profile_id")

        res_4 = global_armoriq.invoke("opportunity_scout", global_keypairs["opportunity_scout"], tok_scout, root_kp, "mcp_scout.scout_and_store_opportunities", {"profile_id": profile_id}, scout_and_store_opportunities)

        res_5 = global_armoriq.invoke("opportunity_ranker", global_keypairs["opportunity_ranker"], tok_ranker, root_kp, "mcp_ranker.rank_and_store_opportunities", {"profile_id": profile_id}, rank_and_store_opportunities)

        return {
            "status": "success",
            "resume_id": resume_id,
            "profile_id": profile_id,
            "opportunities_found": res_4.get("opportunities_found"),
            "total_ranked": res_5.get("total_ranked"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 2. Direct DB QA Endpoint (No Pipeline Run) ─────────────────────────────
@app.post("/api/query-db")
async def query_db(req: QueryRequest):
    """Answers candidate queries directly from SQLite without pipeline execution."""
    q = req.question.lower()
    conn = get_db()

    if any(k in q for k in ["skill", "tech", "stack", "language", "tool"]):
        row = conn.execute("SELECT tech_stack, preferred_roles FROM profiles ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        if not row:
            return {"answer": "No candidate profile found. Please upload a resume first!"}
        skills = json.loads(row["tech_stack"]) if row["tech_stack"] else []
        roles = json.loads(row["preferred_roles"]) if row["preferred_roles"] else []
        return {"answer": f"Your top skills from DB: {', '.join(skills)}. Preferred roles: {', '.join(roles)}."}

    elif any(k in q for k in ["opportunity", "job", "internship", "rank", "match", "competition"]):
        rows = conn.execute("""
            SELECT r.rank, r.relevance_score, o.title, o.category 
            FROM ranked_opportunities r 
            JOIN opportunities o ON r.opportunity_id = o.id 
            ORDER BY r.rank ASC LIMIT 5
        """).fetchall()
        conn.close()
        if not rows:
            return {"answer": "No ranked opportunities found in DB. Run the opportunity scout first!"}
        top_matches = [f"#{r['rank']} {r['title']} ({r['category']}) - Match Score: {r['relevance_score']}%" for r in rows]
        return {"answer": "Top ranked opportunities from DB:\n" + "\n".join(top_matches)}

    else:
        row = conn.execute("SELECT experience_summary, career_goals FROM profiles ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        if not row:
            return {"answer": "No candidate profile found in DB."}
        return {"answer": f"Summary: {row['experience_summary']}\nCareer Goals: {row['career_goals']}"}


# ── 3. Fetch Latest Profile Endpoint ─────────────────────────────────────────
@app.get("/api/profile/latest")
def get_latest_profile():
    conn = get_db()
    profile = conn.execute("SELECT * FROM profiles ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if not profile:
        return {"status": "error", "message": "No profile found in DB"}

    data = dict(profile)
    for k in ["tech_stack", "interests", "preferred_roles", "search_keywords"]:
        if data.get(k):
            try:
                data[k] = json.loads(data[k])
            except Exception:
                pass
    return {"status": "success", "profile": data}


# ── 4. Fetch Opportunities Endpoint ──────────────────────────────────────────
@app.get("/api/opportunities/latest")
def get_latest_opportunities(category: Optional[str] = None):
    conn = get_db()
    query = """
        SELECT r.rank, r.relevance_score, r.match_reasons, o.title, o.url, o.description, o.category, o.source, o.deadline
        FROM ranked_opportunities r
        JOIN opportunities o ON r.opportunity_id = o.id
    """
    params = []
    if category and category.lower() != "all":
        query += " WHERE LOWER(o.category) = ?"
        params.append(category.lower())

    query += " ORDER BY r.rank ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        item = dict(r)
        if item.get("match_reasons"):
            try:
                item["match_reasons"] = json.loads(item["match_reasons"])
            except Exception:
                pass
        results.append(item)
    return {"status": "success", "count": len(results), "opportunities": results}


# ── 5. Fetch Audit Logs Endpoint ─────────────────────────────────────────────
@app.get("/api/audit-logs")
def get_audit_logs():
    return {"status": "success", "logs": global_armoriq.get_audit_trail()}


# ── 6. Trigger Simulated Attack Endpoint (Hackathon Demo) ────────────────────
@app.post("/api/demo/trigger-attack")
def trigger_attack():
    """Simulates a prompt injection attack on opportunity_scout calling auto_apply_job."""
    root_kp = global_keypairs["root_coordinator_agent"]
    tok_scout = global_armoriq.delegate(
        "root_coordinator_agent", root_kp, "opportunity_scout",
        ["profiles:read", "opportunities:write"], ["mcp_scout.scout_and_store_opportunities"], 300
    )

    try:
        global_armoriq.invoke(
            "opportunity_scout", global_keypairs["opportunity_scout"], tok_scout, root_kp,
            "mcp_scout.auto_apply_job", {"job_id": 99, "credit_card_id": 999}, auto_apply_job
        )
        return {"status": "error", "message": "Attack executed!"}
    except ArmorIQScopeViolationError as e:
        return {
            "status": "blocked",
            "shield": "ARMORIQ_BLOCKED",
            "message": str(e),
            "sub_agent": e.sub_agent_id,
            "attempted_tool": e.requested_tool,
            "allowed_tools": e.allowed_tools,
        }
