"""Resume extraction tool for CareerOS."""

import json
import re


def extract_resume(resume_text: str) -> dict:
    """Extracts structured information from raw resume text.

    Parses a resume into structured fields: name, email, phone,
    education, experience, skills, projects, and certifications.

    Args:
        resume_text: The full raw text content of the resume.

    Returns:
        A dict with structured resume fields.
    """
    # Extract email
    email_match = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', resume_text)
    email = email_match[0] if email_match else ""

    # Extract phone
    phone_match = re.findall(r'[\+]?[\d\s\-\(\)]{10,15}', resume_text)
    phone = phone_match[0].strip() if phone_match else ""

    # Split into lines for section parsing
    lines = resume_text.strip().split('\n')

    # The first non-empty line is typically the name
    name = ""
    for line in lines:
        stripped = line.strip()
        if stripped and '@' not in stripped and not re.match(r'^[\d\+\(\)]', stripped):
            name = stripped
            break

    # Section-based parsing
    sections = {
        "education": [],
        "experience": [],
        "skills": [],
        "projects": [],
        "certifications": [],
    }

    current_section = None
    section_keywords = {
        "education": ["education", "academic", "qualification", "degree", "university", "college"],
        "experience": ["experience", "work history", "employment", "professional experience", "internship"],
        "skills": ["skills", "technical skills", "technologies", "tech stack", "competencies", "tools"],
        "projects": ["projects", "personal projects", "academic projects", "portfolio"],
        "certifications": ["certifications", "certificates", "licenses", "courses", "training"],
    }

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this line is a section header
        lower = stripped.lower().rstrip(':').strip()
        matched_section = None
        for section, keywords in section_keywords.items():
            if any(kw in lower for kw in keywords):
                matched_section = section
                break

        if matched_section:
            current_section = matched_section
            continue

        # Add content to current section
        if current_section and stripped:
            # Skip lines that are just the person's name or contact info
            if stripped != name and '@' not in stripped and not re.match(r'^[\d\+\(\)]{10,}', stripped):
                sections[current_section].append(stripped)

    return {
        "status": "success",
        "name": name,
        "email": email,
        "phone": phone,
        "education": sections["education"],
        "experience": sections["experience"],
        "skills": sections["skills"],
        "projects": sections["projects"],
        "certifications": sections["certifications"],
        "raw_text": resume_text,
    }
