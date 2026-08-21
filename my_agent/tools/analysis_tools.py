"""Resume analysis tool for CareerOS."""

import json


def analyze_resume(resume_data: str) -> dict:
    """Analyzes structured resume data and produces insights.

    Examines the candidate's skills, experience, education, and projects
    to identify strengths, weaknesses, experience level, domain focus,
    and key technologies.

    Args:
        resume_data: A JSON string of the structured resume record
                     (as returned by extract_resume or read from DB).

    Returns:
        A dict with analytical insights about the candidate.
    """
    try:
        data = json.loads(resume_data) if isinstance(resume_data, str) else resume_data
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON in resume_data"}

    skills = data.get("skills", [])
    if isinstance(skills, str):
        try:
            skills = json.loads(skills)
        except json.JSONDecodeError:
            skills = [s.strip() for s in skills.split(",")]

    experience = data.get("experience", [])
    if isinstance(experience, str):
        try:
            experience = json.loads(experience)
        except json.JSONDecodeError:
            experience = [experience]

    education = data.get("education", [])
    if isinstance(education, str):
        try:
            education = json.loads(education)
        except json.JSONDecodeError:
            education = [education]

    projects = data.get("projects", [])
    if isinstance(projects, str):
        try:
            projects = json.loads(projects)
        except json.JSONDecodeError:
            projects = [projects]

    certifications = data.get("certifications", [])
    if isinstance(certifications, str):
        try:
            certifications = json.loads(certifications)
        except json.JSONDecodeError:
            certifications = [certifications]

    # Determine experience level
    exp_count = len(experience)
    if exp_count == 0:
        experience_level = "fresher"
    elif exp_count <= 2:
        experience_level = "junior"
    elif exp_count <= 5:
        experience_level = "mid"
    else:
        experience_level = "senior"

    # Identify key technologies from skills
    key_technologies = skills[:10] if skills else []

    # Flatten list items to strings (items may be dicts from LLM extraction)
    def _to_str_list(items):
        result = []
        for item in items:
            if isinstance(item, dict):
                result.append(" ".join(str(v) for v in item.values()))
            else:
                result.append(str(item))
        return result

    all_text = " ".join(_to_str_list(skills) + _to_str_list(projects) + _to_str_list(experience)).lower()
    domain_keywords = {
        "web development": ["html", "css", "javascript", "react", "angular", "vue", "node", "django", "flask", "frontend", "backend", "fullstack"],
        "data science": ["data", "machine learning", "ml", "deep learning", "pandas", "numpy", "tensorflow", "pytorch", "scikit", "analytics"],
        "mobile development": ["android", "ios", "flutter", "react native", "swift", "kotlin", "mobile"],
        "cloud & devops": ["aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "devops", "terraform", "jenkins"],
        "cybersecurity": ["security", "penetration", "cryptography", "firewall", "soc", "vulnerability"],
        "AI/ML": ["ai", "artificial intelligence", "nlp", "computer vision", "generative", "llm", "gpt", "transformer"],
        "blockchain": ["blockchain", "solidity", "ethereum", "web3", "smart contract", "defi"],
        "embedded systems": ["embedded", "iot", "arduino", "raspberry", "microcontroller", "firmware"],
    }

    domain_scores = {}
    for domain, keywords in domain_keywords.items():
        score = sum(1 for kw in keywords if kw in all_text)
        if score > 0:
            domain_scores[domain] = score

    domain_focus = max(domain_scores, key=domain_scores.get) if domain_scores else "general software development"

    # Identify strengths
    strengths = []
    if len(skills) >= 5:
        strengths.append(f"Strong technical breadth with {len(skills)} skills listed")
    if len(projects) >= 2:
        strengths.append(f"Hands-on project experience ({len(projects)} projects)")
    if certifications:
        strengths.append(f"Professional certifications ({len(certifications)})")
    if education:
        strengths.append("Formal education background")
    if experience:
        strengths.append(f"Professional experience ({len(experience)} roles)")
    if not strengths:
        strengths.append("Demonstrates initiative by having a resume ready")

    # Identify weaknesses
    weaknesses = []
    if len(skills) < 3:
        weaknesses.append("Limited technical skills listed")
    if not projects:
        weaknesses.append("No projects mentioned — hands-on work is important")
    if not experience:
        weaknesses.append("No professional experience listed")
    if not certifications:
        weaknesses.append("No certifications — consider adding industry-recognized certs")
    if not weaknesses:
        weaknesses.append("Well-rounded profile with no major gaps")

    # Build summary
    name = data.get("name", "Candidate")
    summary = (
        f"{name} is a {experience_level}-level candidate focused on {domain_focus}. "
        f"They have {len(skills)} skills, {len(projects)} projects, and {len(experience)} work experiences listed. "
        f"Key strengths: {', '.join(strengths[:3])}."
    )

    return {
        "status": "success",
        "strengths": strengths,
        "weaknesses": weaknesses,
        "experience_level": experience_level,
        "domain_focus": domain_focus,
        "key_technologies": key_technologies,
        "summary": summary,
    }
