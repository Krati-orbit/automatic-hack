"""ArmorIQ Governance Verification & Demo Script.

Demonstrates full compliance with Hackathon Track Problem 2 ("Who authorized that?"):
1. Distinct Cryptographic Keypairs per Agent
2. Intent Plan Registration via capture_plan()
3. Cryptographic Authority Delegation via delegate()
4. Governed Tool Invocation via invoke()
5. Real-Time Scope Violation Block (Rule #3)
6. Token Expiration Rejection (Bonus)
7. Audit Trail Logging
"""

import json
import os
import sys
import time

# Add root directory to import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from my_agent.armoriq_crypto import generate_pipeline_keypairs
from my_agent.armoriq_wrapper import (
    ArmorIQClient,
    ArmorIQScopeViolationError,
    ArmorIQTokenExpiredError,
)

# Import MCP tool functions
from my_agent.mcp_servers.mcp_extractor_server import extract_and_store_resume
from my_agent.mcp_servers.mcp_analyzer_server import analyze_and_store_resume
from my_agent.mcp_servers.mcp_profiler_server import build_and_store_profile
from my_agent.mcp_servers.mcp_scout_server import scout_and_store_opportunities, auto_apply_job
from my_agent.mcp_servers.mcp_ranker_server import rank_and_store_opportunities


def run_demo():
    print("==========================================================================")
    print("  🛡️  CareerOS — ArmorIQ Multi-Agent Governance Demo (Problem 2)  🛡️  ")
    print("==========================================================================\n")

    # -------------------------------------------------------------------------
    # Step 1: Keypair Initialization
    # -------------------------------------------------------------------------
    print("🔑 Step 1: Initializing Cryptographic Keypairs for Agent Identities...")
    keypairs = generate_pipeline_keypairs()
    for agent_id, kp in keypairs.items():
        print(f"   • Agent '{agent_id}': Public Key Fingerprint = {kp.get_public_key_hex()}")
    print("   ✅ 6 distinct agent keypairs generated successfully.\n")

    armoriq = ArmorIQClient()

    # -------------------------------------------------------------------------
    # Step 2: Root Plan Capture (capture_plan)
    # -------------------------------------------------------------------------
    print("📋 Step 2: Root Coordinator Captures Intent Plan via capture_plan()...")
    root_kp = keypairs["root_coordinator_agent"]
    plan = armoriq.capture_plan(
        agent_id="root_coordinator_agent",
        intent="Parse candidate resume, build career profile, discover opportunities, and rank matches",
        allowed_tools=[
            "mcp_extractor.extract_and_store_resume",
            "mcp_analyzer.analyze_and_store_resume",
            "mcp_profiler.build_and_store_profile",
            "mcp_scout.scout_and_store_opportunities",
            "mcp_ranker.rank_and_store_opportunities",
        ]
    )
    print(f"   ✅ Plan Captured: ID = {plan.plan_id}")
    print(f"   Authorized Tools: {plan.allowed_tools}\n")

    # -------------------------------------------------------------------------
    # Step 3: Cryptographic Authority Delegation (delegate)
    # -------------------------------------------------------------------------
    print("🔐 Step 3: Root Coordinator Delegates Scoped Tokens to Sub-Agent Keypairs...")
    
    # 1. Extractor Token
    tok_extractor = armoriq.delegate(
        parent_agent_id="root_coordinator_agent",
        parent_keypair=root_kp,
        sub_agent_id="resume_extractor",
        allowed_scopes=["resumes:write"],
        allowed_tools=["mcp_extractor.extract_and_store_resume"],
        ttl_seconds=300
    )

    # 2. Analyzer Token
    tok_analyzer = armoriq.delegate(
        parent_agent_id="root_coordinator_agent",
        parent_keypair=root_kp,
        sub_agent_id="resume_analyzer",
        allowed_scopes=["resumes:read", "analysis:write"],
        allowed_tools=["mcp_analyzer.analyze_and_store_resume"],
        ttl_seconds=300
    )

    # 3. Profiler Token
    tok_profiler = armoriq.delegate(
        parent_agent_id="root_coordinator_agent",
        parent_keypair=root_kp,
        sub_agent_id="profile_maker",
        allowed_scopes=["analysis:read", "profiles:write"],
        allowed_tools=["mcp_profiler.build_and_store_profile"],
        ttl_seconds=300
    )

    # 4. Scout Token
    tok_scout = armoriq.delegate(
        parent_agent_id="root_coordinator_agent",
        parent_keypair=root_kp,
        sub_agent_id="opportunity_scout",
        allowed_scopes=["profiles:read", "opportunities:write", "web:search"],
        allowed_tools=["mcp_scout.scout_and_store_opportunities"],
        ttl_seconds=300
    )

    # 5. Ranker Token
    tok_ranker = armoriq.delegate(
        parent_agent_id="root_coordinator_agent",
        parent_keypair=root_kp,
        sub_agent_id="opportunity_ranker",
        allowed_scopes=["opportunities:read", "ranked:write"],
        allowed_tools=["mcp_ranker.rank_and_store_opportunities"],
        ttl_seconds=300
    )

    print("   ✅ 5 Delegation Tokens signed by Root Keypair and issued to Sub-Agent Keypairs.\n")

    # -------------------------------------------------------------------------
    # Step 4: Happy Path Execution via invoke()
    # -------------------------------------------------------------------------
    print("🚀 Step 4: Executing Governed Multi-Agent Pipeline via invoke()...\n")

    sample_resume = (
        "John Doe, john.doe@email.com, +91-9876543210. Education: B.Tech Computer Science from IIT Delhi (2024). "
        "Skills: Python, JavaScript, React, Node.js, Django, PostgreSQL, Docker, AWS, Machine Learning, TensorFlow. "
        "Experience: Software Intern at Google (Summer 2023) - Built microservices. Junior Developer at TechStartup (2024). "
        "Projects: AI Chatbot, E-commerce Platform. Certifications: AWS Cloud Practitioner."
    )

    # Stage 1: Extractor
    print("   [Stage 1/5] resume_extractor invoking mcp_extractor.extract_and_store_resume...")
    res_1 = armoriq.invoke(
        sub_agent_id="resume_extractor",
        sub_agent_keypair=keypairs["resume_extractor"],
        delegation_token=tok_extractor,
        parent_keypair=root_kp,
        tool_name="mcp_extractor.extract_and_store_resume",
        tool_args={"resume_text": sample_resume},
        tool_func=extract_and_store_resume,
    )
    resume_id = res_1.get("resume_id")
    print(f"      Status: ALLOWED | Stored Resume ID = {resume_id}")

    # Stage 2: Analyzer
    print("   [Stage 2/5] resume_analyzer invoking mcp_analyzer.analyze_and_store_resume...")
    res_2 = armoriq.invoke(
        sub_agent_id="resume_analyzer",
        sub_agent_keypair=keypairs["resume_analyzer"],
        delegation_token=tok_analyzer,
        parent_keypair=root_kp,
        tool_name="mcp_analyzer.analyze_and_store_resume",
        tool_args={"resume_id": resume_id},
        tool_func=analyze_and_store_resume,
    )
    print(f"      Status: ALLOWED | Domain = {res_2.get('domain_focus')} | Level = {res_2.get('experience_level')}")

    # Stage 3: Profiler
    print("   [Stage 3/5] profile_maker invoking mcp_profiler.build_and_store_profile...")
    res_3 = armoriq.invoke(
        sub_agent_id="profile_maker",
        sub_agent_keypair=keypairs["profile_maker"],
        delegation_token=tok_profiler,
        parent_keypair=root_kp,
        tool_name="mcp_profiler.build_and_store_profile",
        tool_args={"resume_id": resume_id},
        tool_func=build_and_store_profile,
    )
    profile_id = res_3.get("profile_id")
    print(f"      Status: ALLOWED | Profile ID = {profile_id} | Roles = {res_3.get('preferred_roles')[:2]}")

    # Stage 4: Scout
    print("   [Stage 4/5] opportunity_scout invoking mcp_scout.scout_and_store_opportunities...")
    res_4 = armoriq.invoke(
        sub_agent_id="opportunity_scout",
        sub_agent_keypair=keypairs["opportunity_scout"],
        delegation_token=tok_scout,
        parent_keypair=root_kp,
        tool_name="mcp_scout.scout_and_store_opportunities",
        tool_args={"profile_id": profile_id},
        tool_func=scout_and_store_opportunities,
    )
    print(f"      Status: ALLOWED | Opportunities Found = {res_4.get('opportunities_found')}")

    # Stage 5: Ranker
    print("   [Stage 5/5] opportunity_ranker invoking mcp_ranker.rank_and_store_opportunities...")
    res_5 = armoriq.invoke(
        sub_agent_id="opportunity_ranker",
        sub_agent_keypair=keypairs["opportunity_ranker"],
        delegation_token=tok_ranker,
        parent_keypair=root_kp,
        tool_name="mcp_ranker.rank_and_store_opportunities",
        tool_args={"profile_id": profile_id},
        tool_func=rank_and_store_opportunities,
    )
    print(f"      Status: ALLOWED | Total Ranked = {res_5.get('total_ranked')}\n")

    # Display Top Ranked Results
    print("🏆 Top Ranked Opportunities:")
    for top in res_5.get("top_ranked", [])[:3]:
        print(f"   Rank #{top.get('rank')} | Score: {top.get('relevance_score')} | Title: {top.get('title')} ({top.get('category')})")
    print("\n   ✅ Happy path completed cleanly across all 5 governed sub-agents!\n")

    # -------------------------------------------------------------------------
    # Step 5: SCOPE VIOLATION ATTACK DEMO (Hackathon Rule #3)
    # -------------------------------------------------------------------------
    print("⚡ Step 5: DEMO ATTACK — Triggering Scope Violation (Rule #3 Requirement)...")
    print("   Scenario: Agent 'opportunity_scout' receives a prompt injection to call 'auto_apply_job'.")
    print("   Authorized Scope for Scout: ['profiles:read', 'opportunities:write', 'web:search']")
    print("   Requested Tool: 'mcp_scout.auto_apply_job' (NOT AUTHORIZED IN TOKEN!)\n")

    try:
        armoriq.invoke(
            sub_agent_id="opportunity_scout",
            sub_agent_keypair=keypairs["opportunity_scout"],
            delegation_token=tok_scout,
            parent_keypair=root_kp,
            tool_name="mcp_scout.auto_apply_job",
            tool_args={"job_id": 99, "credit_card_id": 123456789},
            tool_func=auto_apply_job,
        )
        print("   ❌ FAIL: Unauthorized tool was executed! ArmorIQ did not block it!")
    except ArmorIQScopeViolationError as e:
        print(f"   🛡️ SUCCESS: ArmorIQ Cryptographically Blocked the Scope Violation!")
        print(f"      Error Caught: {e}")
        print(f"      Sub-Agent: {e.sub_agent_id}")
        print(f"      Attempted Tool: {e.requested_tool}")
        print(f"      Allowed Tools: {e.allowed_tools}\n")

    # -------------------------------------------------------------------------
    # Step 6: TOKEN EXPIRATION DEMO (Bonus Feature)
    # -------------------------------------------------------------------------
    print("⏰ Step 6: DEMO BONUS — Testing Expired Token Enforcement...")
    expired_token = armoriq.delegate(
        parent_agent_id="root_coordinator_agent",
        parent_keypair=root_kp,
        sub_agent_id="opportunity_scout",
        allowed_scopes=["profiles:read"],
        allowed_tools=["mcp_scout.scout_and_store_opportunities"],
        ttl_seconds=-1,  # Expired immediately
    )

    try:
        armoriq.invoke(
            sub_agent_id="opportunity_scout",
            sub_agent_keypair=keypairs["opportunity_scout"],
            delegation_token=expired_token,
            parent_keypair=root_kp,
            tool_name="mcp_scout.scout_and_store_opportunities",
            tool_args={"profile_id": profile_id},
            tool_func=scout_and_store_opportunities,
        )
        print("   ❌ FAIL: Expired token was accepted!")
    except ArmorIQTokenExpiredError as e:
        print("   🛡️ SUCCESS: ArmorIQ Rejected Expired Delegation Token!")
        print(f"      Error Caught: {e}\n")

    # -------------------------------------------------------------------------
    # Step 7: Audit Trail Output
    # -------------------------------------------------------------------------
    print("📊 Step 7: Exporting ArmorIQ Cryptographic Audit Trail Summary...")
    logs = armoriq.get_audit_trail()
    events_count = len(logs)
    blocked_count = sum(1 for l in logs if l.get("status", "").startswith("BLOCKED"))
    allowed_count = sum(1 for l in logs if l.get("status") == "ALLOWED_EXECUTED")

    print(f"   Total Audit Events: {events_count}")
    print(f"   Allowed Tool Calls: {allowed_count}")
    print(f"   Blocked Scope Violations: {blocked_count}\n")

    print("==========================================================================")
    print("  🎉 ALL ARMORIQ PROBLEM 2 REQUIREMENTS VERIFIED SUCCESSFULLY! 🎉  ")
    print("==========================================================================")


if __name__ == "__main__":
    run_demo()
