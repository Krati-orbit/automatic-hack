"""MCP Server Tool for Sub-Agent 1: resume_extractor."""

from ..tools.resume_tools import extract_resume
from ..tools.db_tools import store_to_db


def extract_and_store_resume(resume_text: str) -> dict:
    """Parses resume text into structured fields and stores it in the DB.

    Authorized Scope: 'resumes:write'
    """
    extracted = extract_resume(resume_text)
    if extracted.get("status") == "error":
        return extracted

    db_result = store_to_db("resumes", extracted)
    return {
        "status": "success",
        "resume_id": db_result.get("id"),
        "name": extracted.get("name"),
        "email": extracted.get("email"),
        "skills_count": len(extracted.get("skills", [])),
    }
