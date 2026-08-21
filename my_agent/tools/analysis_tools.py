"""Resume analysis tool for CareerOS powered by LiteLLM & Groq Cloud LLM."""

import json
from .llm_tools import call_groq_llm_json


def analyze_resume(resume_data: str) -> dict:
    """Analyzes structured resume data and produces deep AI insights using Groq Cloud LLM.

    Identifies candidate strengths, weaknesses, experience level, domain focus, and key technologies.
    """
    try:
        data = json.loads(resume_data) if isinstance(resume_data, str) else resume_data
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON in resume_data"}

    prompt = f"""
Analyze the following candidate resume data and return a JSON object with these exact keys:
"strengths": (list of 3-5 specific candidate strengths),
"weaknesses": (list of 2-3 specific growth/weakness areas),
"experience_level": (string: one of ["fresher", "junior", "mid", "senior"]),
"domain_focus": (string: primary domain, e.g. "Full Stack Web Development", "AI/ML Engineering", "Cloud DevOps"),
"key_technologies": (list of top 5-10 technologies mastered),
"summary": (string: 2-3 sentence executive AI career summary of candidate).

CANDIDATE DATA:
{json.dumps(data, indent=2)[:3500]}
"""

    llm_res = call_groq_llm_json(prompt, system_instruction="You are a Senior Technical Recruiter and AI Career Advisor. Return valid JSON only.")

    if llm_res and llm_res.get("summary"):
        return {
            "status": "success",
            "strengths": llm_res.get("strengths") or ["Strong technical skills"],
            "weaknesses": llm_res.get("weaknesses") or ["Expand industry certifications"],
            "experience_level": llm_res.get("experience_level") or "mid",
            "domain_focus": llm_res.get("domain_focus") or "Software Engineering",
            "key_technologies": llm_res.get("key_technologies") or data.get("skills", []),
            "summary": llm_res.get("summary") or f"Candidate skilled in {', '.join(data.get('skills', [])[:3])}.",
            "llm_engine": "groq_openai_gpt_oss_20b"
        }

    # Fallback if LLM response was empty
    skills = data.get("skills", [])
    return {
        "status": "success",
        "strengths": ["Solid technical foundation", "Demonstrates initiative"],
        "weaknesses": ["Consider building more open-source portfolio projects"],
        "experience_level": "mid",
        "domain_focus": "Software Development",
        "key_technologies": skills[:8] if isinstance(skills, list) else [skills],
        "summary": f"{data.get('name', 'Candidate')} is a software developer with skills in {', '.join(skills[:3]) if isinstance(skills, list) else skills}.",
        "llm_engine": "rule_fallback"
    }
