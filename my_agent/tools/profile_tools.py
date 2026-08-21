"""Profile maker tool for CareerOS."""

import json


def make_profile(resume_data: str, analysis_data: str) -> dict:
    """Builds a structured candidate profile from resume and analysis data.

    Combines raw resume information with analytical insights to produce
    a structured profile containing tech stack, interests, career goals,
    preferred roles, and search keywords for opportunity matching.

    Args:
        resume_data: A JSON string of the structured resume record.
        analysis_data: A JSON string of the resume analysis record.

    Returns:
        A dict with the structured candidate profile.
    """
    try:
        resume = json.loads(resume_data) if isinstance(resume_data, str) else resume_data
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON in resume_data"}

    try:
        analysis = json.loads(analysis_data) if isinstance(analysis_data, str) else analysis_data
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON in analysis_data"}

    # Extract skills as tech stack
    skills = resume.get("skills", [])
    if isinstance(skills, str):
        try:
            skills = json.loads(skills)
        except json.JSONDecodeError:
            skills = [s.strip() for s in skills.split(",")]

    tech_stack = skills[:15]  # Top 15 skills as tech stack

    # Determine domain focus and interests
    domain_focus = analysis.get("domain_focus", "software development")
    key_technologies = analysis.get("key_technologies", [])
    experience_level = analysis.get("experience_level", "fresher")

    # Build interests from domain focus and project areas
    interests = [domain_focus]
    projects = resume.get("projects", [])
    if isinstance(projects, str):
        try:
            projects = json.loads(projects)
        except json.JSONDecodeError:
            projects = [projects]

    # Add unique interest areas from projects
    interest_keywords = {
        "open source": ["open source", "github", "contribution", "oss"],
        "hackathons": ["hackathon", "contest", "competition"],
        "AI/ML": ["ai", "ml", "machine learning", "deep learning", "neural"],
        "web development": ["web", "website", "frontend", "backend", "fullstack"],
        "mobile apps": ["mobile", "android", "ios", "app"],
        "data science": ["data", "analytics", "visualization", "statistics"],
        "cloud computing": ["cloud", "aws", "azure", "gcp", "serverless"],
        "blockchain": ["blockchain", "crypto", "web3", "smart contract"],
    }

    all_text = " ".join(str(p) for p in projects + skills).lower()
    for interest, keywords in interest_keywords.items():
        if any(kw in all_text for kw in keywords) and interest not in interests:
            interests.append(interest)

    # Determine career goals based on experience level and domain
    role_mapping = {
        "web development": ["Frontend Developer", "Backend Developer", "Full Stack Developer", "Web Developer"],
        "data science": ["Data Scientist", "Data Analyst", "ML Engineer", "Business Analyst"],
        "mobile development": ["Android Developer", "iOS Developer", "Mobile Developer", "Flutter Developer"],
        "cloud & devops": ["DevOps Engineer", "Cloud Engineer", "SRE", "Platform Engineer"],
        "cybersecurity": ["Security Analyst", "Penetration Tester", "Security Engineer", "SOC Analyst"],
        "AI/ML": ["ML Engineer", "AI Researcher", "NLP Engineer", "Computer Vision Engineer"],
        "blockchain": ["Blockchain Developer", "Smart Contract Developer", "Web3 Developer"],
        "embedded systems": ["Embedded Engineer", "IoT Developer", "Firmware Engineer"],
        "general software development": ["Software Developer", "Software Engineer", "Programmer"],
    }

    preferred_roles = role_mapping.get(domain_focus, ["Software Developer", "Software Engineer"])

    # Career goals
    level_goals = {
        "fresher": f"Seeking entry-level opportunities in {domain_focus} to build industry experience",
        "junior": f"Looking to grow as a {preferred_roles[0]} with hands-on project work",
        "mid": f"Aiming for senior roles in {domain_focus} with leadership opportunities",
        "senior": f"Targeting lead/architect positions in {domain_focus}",
    }
    career_goals = level_goals.get(experience_level, f"Exploring opportunities in {domain_focus}")

    # Experience summary
    name = resume.get("name", "Candidate")
    experience = resume.get("experience", [])
    if isinstance(experience, str):
        try:
            experience = json.loads(experience)
        except json.JSONDecodeError:
            experience = [experience]

    experience_summary = (
        f"{name} is a {experience_level}-level professional with expertise in "
        f"{', '.join(tech_stack[:5])}. "
        f"Has {len(experience)} work experience(s) and {len(projects)} project(s)."
    )

    # Build search keywords for opportunity scout
    search_keywords = []
    # Add role-based keywords
    for role in preferred_roles[:3]:
        search_keywords.append(f"{role} {experience_level}")
    # Add tech-based keywords
    for tech in key_technologies[:5]:
        search_keywords.append(f"{tech} jobs")
    # Add general opportunity keywords
    search_keywords.extend([
        f"{domain_focus} internship",
        f"{domain_focus} hackathon",
        f"{domain_focus} competition",
        f"tech conclave {domain_focus}",
    ])

    return {
        "status": "success",
        "name": name,
        "tech_stack": tech_stack,
        "interests": interests,
        "career_goals": career_goals,
        "preferred_roles": preferred_roles,
        "experience_summary": experience_summary,
        "location_preference": "remote",  # Default; can be enhanced later
        "search_keywords": search_keywords,
    }
