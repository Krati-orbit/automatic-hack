"""FastAPI Backend Server for CareerOS.

Exposes REST API endpoints for multi-user relational candidate intelligence:
- /api/upload-resume-pdf: Accepts PDF file upload, extracts text, and triggers 5-stage pipeline
- /api/process-resume: Triggers the ArmorIQ governed 5-stage pipeline
- /api/query-db: Direct DB QA queries (answering profile/skills queries with optional profile_id filter)
- /api/profiles: Lists all candidate profiles in SQLite
- /api/profiles/{profile_id}: Fetches complete relational user payload
- /api/resumes: Lists all parsed candidate resumes
- /api/resumes/{resume_id}: Fetches detailed resume & AI analysis breakdown
- /api/profiles/{profile_id}/opportunities: Fetches opportunities scored for profile_id
- /api/audit-logs: Fetches live ArmorIQ governance audit trail logs
- /api/demo/trigger-attack: Simulates prompt injection attack with ArmorIQ Shield ON/OFF toggle
"""

import io
import json
import os
import sqlite3
import sys
import time
from typing import Optional

from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from my_agent.armoriq_crypto import generate_pipeline_keypairs
from my_agent.armoriq_wrapper import ArmorIQClient, ArmorIQScopeViolationError
from my_agent.mcp_servers.mcp_extractor_server import extract_and_store_resume
from my_agent.mcp_servers.mcp_analyzer_server import analyze_and_store_resume
from my_agent.mcp_servers.mcp_profiler_server import build_and_store_profile
from my_agent.mcp_servers.mcp_scout_server import scout_and_store_opportunities, auto_apply_job
from my_agent.mcp_servers.mcp_ranker_server import rank_and_store_opportunities

app = FastAPI(title="CareerOS API Server", version="2.0")

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
    profile_id: Optional[int] = None


class AttackRequest(BaseModel):
    secured: Optional[bool] = True


# ── Root Welcome Endpoint ───────────────────────────────────────────────────
@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "CareerOS ArmorIQ Governed API Server",
        "version": "2.0",
        "documentation": "/docs",
        "endpoints": {
            "upload_pdf": "/api/upload-resume-pdf (POST)",
            "process_resume": "/api/process-resume (POST)",
            "query_db": "/api/query-db (POST)",
            "profiles_list": "/api/profiles (GET)",
            "profile_by_id": "/api/profiles/{profile_id} (GET)",
            "resumes_list": "/api/resumes (GET)",
            "resume_by_id": "/api/resumes/{resume_id} (GET)",
            "user_opportunities": "/api/profiles/{profile_id}/opportunities (GET)",
            "latest_profile": "/api/profile/latest (GET)",
            "latest_opportunities": "/api/opportunities/latest (GET)",
            "audit_logs": "/api/audit-logs (GET)",
            "trigger_attack": "/api/demo/trigger-attack (POST)"
        }
    }


def trigger_adk_web_background(resume_text: str) -> dict:
    """Triggers background execution call to Google ADK Web Server (http://127.0.0.1:8080)."""
    import urllib.request
    import threading

    def _fire_adk_run(session_id, text):
        try:
            run_body = json.dumps({
                "appName": "my_agent",
                "userId": "frontend_user",
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": f"Process candidate resume text: {text[:400]}"}]
                }
            }).encode("utf-8")
            req = urllib.request.Request(
                "http://127.0.0.1:8080/run",
                data=run_body,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp.read()
        except Exception as err:
            print(f"[ADK Background Sync Log] {err}")

    try:
        # Create ADK Session
        req1 = urllib.request.Request(
            "http://127.0.0.1:8080/apps/my_agent/users/frontend_user/sessions",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req1, timeout=3) as resp1:
            sess_data = json.loads(resp1.read().decode("utf-8"))
            session_id = sess_data.get("id")

        if not session_id:
            return {"status": "error", "message": "Could not create ADK session"}

        # Fire background execution thread so main response returns instantly
        t = threading.Thread(target=_fire_adk_run, args=(session_id, resume_text), daemon=True)
        t.start()

        return {
            "status": "success",
            "adk_server_url": "http://127.0.0.1:8080",
            "app_name": "my_agent",
            "session_id": session_id,
            "events_count": 1,
            "events_preview": "ADK Root Agent session triggered on port 8080",
        }
    except Exception as e:
        return {
            "status": "active_offline_fallback",
            "adk_server_url": "http://127.0.0.1:8080",
            "app_name": "my_agent",
            "session_id": "adk_bg_sync_local",
            "events_preview": f"ADK Web Server Background Trigger Logged ({str(e)})"
        }


# ── 1. Process Resume Endpoint (Full Pipeline) ──────────────────────────────
@app.post("/api/process-resume")
async def process_resume(resume_text: str = Form(...)):
    """Executes the 5-stage governed pipeline with ArmorIQ SDK and ADK Web sync."""
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

        # Trigger background execution call to ADK Web Server (port 8080)
        adk_sync = trigger_adk_web_background(resume_text)

        return {
            "status": "success",
            "resume_id": resume_id,
            "profile_id": profile_id,
            "opportunities_found": res_4.get("opportunities_found"),
            "total_ranked": res_5.get("total_ranked"),
            "adk_execution": adk_sync
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 1B. Upload PDF Resume Endpoint ──────────────────────────────────────────
@app.post("/api/upload-resume-pdf")
async def upload_resume_pdf(file: UploadFile = File(...)):
    """Extracts text from an uploaded PDF resume and executes the 5-stage pipeline."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted.")

    try:
        contents = await file.read()
        extracted_text = ""

        # Attempt 1: Try pypdf extraction
        try:
            pdf_file = io.BytesIO(contents)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    extracted_text += t + "\n"
        except Exception:
            pass

        # Attempt 2: Fallback to plain text decoding (handles plain text saved as .pdf)
        if not extracted_text.strip():
            try:
                extracted_text = contents.decode("utf-8", errors="ignore")
            except Exception:
                pass

        # Clean unprintable null characters
        extracted_text = extracted_text.replace("\x00", "").strip()

        if not extracted_text:
            raise HTTPException(status_code=400, detail="Could not extract readable text from uploaded PDF file.")

        result = await process_resume(resume_text=extracted_text)
        result["extracted_text_preview"] = extracted_text[:300]
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing error: {str(e)}")




# ── 2. Direct DB QA Endpoint ────────────────────────────────────────────────
@app.post("/api/query-db")
async def query_db(req: QueryRequest):
    """Answers candidate queries directly from SQLite with optional profile_id filter."""
    q = req.question.lower()
    conn = get_db()
    pid = req.profile_id

    if any(k in q for k in ["skill", "tech", "stack", "language", "tool"]):
        sql = "SELECT tech_stack, preferred_roles FROM profiles"
        params = []
        if pid:
            sql += " WHERE id = ?"
            params.append(pid)
        sql += " ORDER BY id DESC LIMIT 1"
        row = conn.execute(sql, params).fetchone()
        conn.close()
        if not row:
            return {"answer": "No candidate profile found. Please select or upload a profile first!"}
        skills = json.loads(row["tech_stack"]) if row["tech_stack"] else []
        roles = json.loads(row["preferred_roles"]) if row["preferred_roles"] else []
        return {"answer": f"Top technical skills in DB: {', '.join(skills)}. Preferred roles: {', '.join(roles)}."}

    elif any(k in q for k in ["opportunity", "job", "internship", "rank", "match", "competition"]):
        sql = """
            SELECT r.rank, r.relevance_score, o.title, o.category 
            FROM ranked_opportunities r 
            JOIN opportunities o ON r.opportunity_id = o.id 
        """
        params = []
        if pid:
            sql += " WHERE r.profile_id = ?"
            params.append(pid)
        sql += " ORDER BY r.rank ASC LIMIT 5"
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        if not rows:
            return {"answer": "No ranked opportunities found for this profile in DB."}
        top_matches = [f"#{r['rank']} {r['title']} ({r['category']}) - Match Score: {r['relevance_score']}% font match" for r in rows]
        return {"answer": "Top ranked opportunities from DB:\n" + "\n".join(top_matches)}

    else:
        sql = "SELECT experience_summary, career_goals FROM profiles"
        params = []
        if pid:
            sql += " WHERE id = ?"
            params.append(pid)
        sql += " ORDER BY id DESC LIMIT 1"
        row = conn.execute(sql, params).fetchone()
        conn.close()
        if not row:
            return {"answer": "No candidate profile details found in DB."}
        return {"answer": f"Experience Summary: {row['experience_summary']}\nCareer Goals: {row['career_goals']}"}


# ── 3. List All Profiles Endpoint ───────────────────────────────────────────
@app.get("/api/profiles")
def get_all_profiles():
    """Lists all candidate profiles with linked resume metadata."""
    conn = get_db()
    rows = conn.execute("""
        SELECT p.id as profile_id, p.resume_id, p.tech_stack, p.preferred_roles, p.experience_summary, p.created_at,
               r.name as candidate_name, r.email as candidate_email, r.phone as candidate_phone
        FROM profiles p
        LEFT JOIN resumes r ON p.resume_id = r.id
        ORDER BY p.id DESC
    """).fetchall()
    conn.close()

    results = []
    for r in rows:
        item = dict(r)
        for k in ["tech_stack", "preferred_roles"]:
            if item.get(k):
                try:
                    item[k] = json.loads(item[k])
                except Exception:
                    pass
        if not item.get("candidate_name"):
            item["candidate_name"] = f"Candidate Profile #{item['profile_id']}"
        results.append(item)
    return {"status": "success", "count": len(results), "profiles": results}


# ── 4. Get Profile Full Payload By ID ─────────────────────────────────────────
@app.get("/api/profiles/{profile_id}")
def get_profile_by_id(profile_id: int):
    """Fetches complete relational profile payload (profile, resume, analysis, opportunities)."""
    conn = get_db()

    profile_row = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    if not profile_row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Profile #{profile_id} not found")

    profile_data = dict(profile_row)
    for k in ["tech_stack", "interests", "preferred_roles", "search_keywords"]:
        if profile_data.get(k):
            try:
                profile_data[k] = json.loads(profile_data[k])
            except Exception:
                pass

    # Fetch linked resume
    resume_row = None
    if profile_data.get("resume_id"):
        resume_row = conn.execute("SELECT * FROM resumes WHERE id = ?", (profile_data["resume_id"],)).fetchone()
    resume_data = dict(resume_row) if resume_row else None
    if resume_data:
        for k in ["education", "experience", "skills", "projects", "certifications"]:
            if resume_data.get(k):
                try:
                    resume_data[k] = json.loads(resume_data[k])
                except Exception:
                    pass

    # Fetch linked analysis
    analysis_row = None
    if profile_data.get("resume_id"):
        analysis_row = conn.execute("SELECT * FROM resume_analysis WHERE resume_id = ?", (profile_data["resume_id"],)).fetchone()
    analysis_data = dict(analysis_row) if analysis_row else None
    if analysis_data:
        for k in ["strengths", "weaknesses", "key_technologies"]:
            if analysis_data.get(k):
                try:
                    analysis_data[k] = json.loads(analysis_data[k])
                except Exception:
                    pass

    # Fetch ranked opportunities count and items
    opp_rows = conn.execute("""
        SELECT r.rank, r.relevance_score, r.match_reasons, o.id as opportunity_id, o.title, o.url, o.description, o.category, o.source, o.deadline
        FROM ranked_opportunities r
        JOIN opportunities o ON r.opportunity_id = o.id
        WHERE r.profile_id = ?
        ORDER BY r.rank ASC
    """, (profile_id,)).fetchall()
    
    opportunities = []
    for r in opp_rows:
        item = dict(r)
        if item.get("match_reasons"):
            try:
                item["match_reasons"] = json.loads(item["match_reasons"])
            except Exception:
                pass
        opportunities.append(item)

    conn.close()

    return {
        "status": "success",
        "profile": profile_data,
        "resume": resume_data,
        "analysis": analysis_data,
        "opportunities_count": len(opportunities),
        "opportunities": opportunities
    }


# ── 5. List All Resumes Endpoint ─────────────────────────────────────────────
@app.get("/api/resumes")
def get_all_resumes():
    """Lists all parsed resumes with associated analysis."""
    conn = get_db()
    rows = conn.execute("""
        SELECT r.*, a.experience_level, a.domain_focus, a.strengths, a.weaknesses, a.summary as analysis_summary
        FROM resumes r
        LEFT JOIN resume_analysis a ON r.id = a.resume_id
        ORDER BY r.id DESC
    """).fetchall()
    conn.close()

    results = []
    for r in rows:
        item = dict(r)
        for k in ["education", "experience", "skills", "projects", "certifications", "strengths", "weaknesses"]:
            if item.get(k):
                try:
                    item[k] = json.loads(item[k])
                except Exception:
                    pass
        results.append(item)
    return {"status": "success", "count": len(results), "resumes": results}


# ── 6. Get Single Resume By ID Endpoint ──────────────────────────────────────
@app.get("/api/resumes/{resume_id}")
def get_resume_by_id(resume_id: int):
    """Fetches detailed resume data and analysis by resume_id."""
    conn = get_db()
    resume_row = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
    if not resume_row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Resume #{resume_id} not found")

    resume_data = dict(resume_row)
    for k in ["education", "experience", "skills", "projects", "certifications"]:
        if resume_data.get(k):
            try:
                resume_data[k] = json.loads(resume_data[k])
            except Exception:
                pass

    analysis_row = conn.execute("SELECT * FROM resume_analysis WHERE resume_id = ?", (resume_id,)).fetchone()
    analysis_data = dict(analysis_row) if analysis_row else None
    if analysis_data:
        for k in ["strengths", "weaknesses", "key_technologies"]:
            if analysis_data.get(k):
                try:
                    analysis_data[k] = json.loads(analysis_data[k])
                except Exception:
                    pass

    conn.close()
    return {"status": "success", "resume": resume_data, "analysis": analysis_data}


# ── 7. Get User Scoped Opportunities ──────────────────────────────────────────
@app.get("/api/profiles/{profile_id}/opportunities")
def get_opportunities_by_profile(profile_id: int, category: Optional[str] = None):
    """Fetches opportunities ranked specifically for candidate profile_id."""
    conn = get_db()
    query = """
        SELECT r.rank, r.relevance_score, r.match_reasons, o.id as opportunity_id, o.title, o.url, o.description, o.category, o.source, o.deadline
        FROM ranked_opportunities r
        JOIN opportunities o ON r.opportunity_id = o.id
        WHERE r.profile_id = ?
    """
    params = [profile_id]

    if category and category.lower() != "all":
        query += " AND LOWER(o.category) = ?"
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


# ── 8. Fetch Latest Profile Endpoint (Fallback) ──────────────────────────────
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


# ── 9. Fetch Opportunities Endpoint (Fallback) ───────────────────────────────
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


# ── 10. Fetch Audit Logs Endpoint ────────────────────────────────────────────
@app.get("/api/audit-logs")
def get_audit_logs():
    return {"status": "success", "logs": global_armoriq.get_audit_trail()}


# ── 11. Trigger Simulated Attack Endpoint (Hackathon Demo) ───────────────────
@app.post("/api/demo/trigger-attack")
def trigger_attack(req: Optional[AttackRequest] = None):
    """Simulates a prompt injection attack on opportunity_scout calling auto_apply_job.
    
    If secured=True (ArmorIQ Shield ON):
        ArmorIQ intercepts and blocks the call before execution, returning full trajectory trace.
    If secured=False (ArmorIQ Shield OFF):
        Bypasses ArmorIQ governance, executing the unauthorized tool without authorization.
    """
    is_secured = req.secured if (req and req.secured is not None) else True
    root_kp = global_keypairs["root_coordinator_agent"]
    tok_scout = global_armoriq.delegate(
        "root_coordinator_agent", root_kp, "opportunity_scout",
        ["profiles:read", "opportunities:write"], ["mcp_scout.scout_and_store_opportunities"], 300
    )

    trajectory_trace = [
        {"step": 1, "node": "Root Coordinator", "action": "Captured Plan & Issued Signed Delegation Token"},
        {"step": 2, "node": "Sub-Agent: opportunity_scout", "action": "Received Delegation Scope: ['mcp_scout.scout_and_store_opportunities']"},
        {"step": 3, "node": "Prompt Injection Attack", "action": "Malicious prompt instructed agent to invoke unauthorized tool: 'mcp_scout.auto_apply_job'"},
    ]

    if is_secured:
        try:
            global_armoriq.invoke(
                "opportunity_scout", global_keypairs["opportunity_scout"], tok_scout, root_kp,
                "mcp_scout.auto_apply_job", {"job_id": 99, "credit_card_id": 999}, auto_apply_job
            )
            return {"status": "error", "message": "Attack executed!"}
        except ArmorIQScopeViolationError as e:
            trajectory_trace.append({
                "step": 4,
                "node": "ArmorIQ Cryptographic Interceptor",
                "action": f"INTERCEPTED & BLOCKED BEFORE EXECUTION! Tool '{e.requested_tool}' is NOT in delegated scope {e.allowed_tools}."
            })
            return {
                "status": "blocked",
                "shield": "ARMORIQ_PROTECTED_ON",
                "message": str(e),
                "sub_agent": e.sub_agent_id,
                "attempted_tool": e.requested_tool,
                "allowed_tools": e.allowed_tools,
                "trajectory_trace": trajectory_trace,
                "timestamp": time.time()
            }
    else:
        # UNSECURED MODE: Bypass ArmorIQ governance check
        global_armoriq._log_audit({
            "event": "UNSECURED_PROMPT_ATTACK_EXPLOITED",
            "sub_agent": "opportunity_scout",
            "requested_tool": "mcp_scout.auto_apply_job",
            "status": "UNPROTECTED_SECURITY_BREACH",
            "reason": "ARMORIQ_SHIELD_DISABLED_BY_USER",
            "timestamp": time.time()
        })
        
        # Execute handler directly without token verification
        res = auto_apply_job(job_id=99, credit_card_id=999)
        trajectory_trace.append({
            "step": 4,
            "node": "Bypassed Security Barrier",
            "action": "ARMORIQ SHIELD OFF! Unauthorized tool 'mcp_scout.auto_apply_job' EXECUTED without cryptographic verification!"
        })
        return {
            "status": "breached",
            "shield": "ARMORIQ_DISABLED_OFF",
            "warning": "UNSECURED BREACH EXPLOITED! Prompt attack executed unauthorized auto_apply_job tool because ArmorIQ Shield was OFF!",
            "sub_agent": "opportunity_scout",
            "attempted_tool": "mcp_scout.auto_apply_job",
            "executed_result": res,
            "trajectory_trace": trajectory_trace,
            "timestamp": time.time()
        }
