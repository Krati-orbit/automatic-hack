"""Resume extraction tool for CareerOS powered by LiteLLM & Groq Cloud LLM."""

import json
import re
from .llm_tools import call_groq_llm_json


def extract_resume(resume_text: str) -> dict:
    """Extracts structured information from raw resume text using Groq Cloud LLM.

    Parses candidate name, email, phone, education, experience, skills, projects, and certifications.
    """
    prompt = f"""
Parse the following resume text into a JSON object with these exact keys:
"name": (string, candidate full name),
"email": (string, candidate email address),
"phone": (string, candidate phone number),
"education": (list of strings, degree/university lines),
"experience": (list of strings, job titles/company lines),
"skills": (list of strings, technical skills, tools, languages),
"projects": (list of strings, project titles and descriptions),
"certifications": (list of strings, certifications or awards).

RESUME TEXT:
{resume_text[:4000]}
"""

    llm_res = call_groq_llm_json(prompt, system_instruction="You are an expert AI Resume Parsing Agent. Return valid JSON only.")

    # Extract email and phone fallback if LLM misses them
    email_match = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', resume_text)
    phone_match = re.findall(r'[\+]?[\d\s\-\(\)]{10,15}', resume_text)

    email_val = llm_res.get("email") or (email_match[0] if email_match else "")
    name = llm_res.get("name") or ""
    
    # Filter out section headers accidentally picked up as names
    invalid_header_words = {"stack", "technical stack", "resume", "cv", "curriculum vitae", "experience", "education", "skills", "summary", "projects", "contact", "profile", "overview", "header"}
    if name and name.lower().strip() in invalid_header_words:
        name = ""

    if not name:
        for line in resume_text.strip().split('\n'):
            stripped = line.strip()
            if stripped and '@' not in stripped and not re.match(r'^[\d\+\(\)]', stripped):
                if stripped.lower() not in invalid_header_words and len(stripped) < 40 and not any(k in stripped.lower() for k in ["stack", "resume", "summary", "skills"]):
                    name = stripped
                    break

    # Final fallback: infer name from email if still missing
    if not name and email_val:
        handle = email_val.split('@')[0]
        clean_handle = re.sub(r'\d+', '', handle).replace('.', ' ').replace('_', ' ').strip().title()
        name = clean_handle if clean_handle else "Candidate"
    elif not name:
        name = "Candidate"

    return {
        "status": "success",
        "name": name,
        "email": llm_res.get("email") or (email_match[0] if email_match else ""),
        "phone": llm_res.get("phone") or (phone_match[0].strip() if phone_match else ""),
        "education": llm_res.get("education") or [],
        "experience": llm_res.get("experience") or [],
        "skills": llm_res.get("skills") or [],
        "projects": llm_res.get("projects") or [],
        "certifications": llm_res.get("certifications") or [],
        "raw_text": resume_text,
        "llm_engine": "groq_openai_gpt_oss_20b"
    }
