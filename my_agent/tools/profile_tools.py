"""Profile maker tool for CareerOS powered by LiteLLM & Groq Cloud LLM."""

import json
from .llm_tools import call_groq_llm_json


def make_profile(resume_data: str, analysis_data: str) -> dict:
    """Builds a structured candidate profile from resume and analysis data using Groq Cloud LLM."""
    try:
        resume = json.loads(resume_data) if isinstance(resume_data, str) else resume_data
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON in resume_data"}

    try:
        analysis = json.loads(analysis_data) if isinstance(analysis_data, str) else analysis_data
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON in analysis_data"}

    prompt = f"""
Generate a structured candidate profile JSON object from the following resume & AI analysis:
"tech_stack": (list of top 10 technical skills/languages),
"interests": (list of 3-5 technical domain interests),
"career_goals": (string: candidate 1-2 sentence career vision),
"preferred_roles": (list of 3-5 target job titles),
"experience_summary": (string: 2-3 sentence executive experience summary),
"search_keywords": (list of 5 targeted opportunity search query phrases, e.g. "React AI Engineer", "Python ML Internship", "Hackathons").

RESUME:
{json.dumps(resume, indent=2)[:2500]}

ANALYSIS:
{json.dumps(analysis, indent=2)[:1500]}
"""

    llm_res = call_groq_llm_json(prompt, system_instruction="You are an AI Profile Generation Agent. Return valid JSON only.")

    name = resume.get("name") or "Candidate"
    skills = resume.get("skills") or []
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",")]

    if llm_res and llm_res.get("tech_stack"):
        return {
            "status": "success",
            "name": name,
            "tech_stack": llm_res.get("tech_stack") or skills[:10],
            "interests": llm_res.get("interests") or [analysis.get("domain_focus", "Software Development")],
            "career_goals": llm_res.get("career_goals") or f"Seeking roles in {analysis.get('domain_focus', 'Tech')}",
            "preferred_roles": llm_res.get("preferred_roles") or ["Software Engineer", "Full Stack Developer"],
            "experience_summary": llm_res.get("experience_summary") or analysis.get("summary", ""),
            "location_preference": "remote",
            "search_keywords": llm_res.get("search_keywords") or [f"{skills[0] if skills else 'Software'} developer"],
            "llm_engine": "groq_openai_gpt_oss_20b"
        }

    # Fallback
    return {
        "status": "success",
        "name": name,
        "tech_stack": skills[:10],
        "interests": [analysis.get("domain_focus", "Software Development")],
        "career_goals": f"Seeking positions as a Software Developer focused on {analysis.get('domain_focus', 'Tech')}.",
        "preferred_roles": ["Software Developer", "Full Stack Engineer"],
        "experience_summary": f"{name} is a candidate skilled in {', '.join(skills[:4])}.",
        "location_preference": "remote",
        "search_keywords": [f"{skills[0] if skills else 'Software'} job"],
        "llm_engine": "rule_fallback"
    }
