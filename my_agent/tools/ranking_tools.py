"""Ranking tool for CareerOS — scores and orders opportunities."""

import json


def rank_results(profile_data: str, opportunities_data: str) -> dict:
    """Scores and ranks opportunities by relevance to the candidate profile.

    Compares each opportunity against the candidate's tech stack, interests,
    preferred roles, and experience level to assign a relevance score (0-100)
    and match reasons.

    Args:
        profile_data: A JSON string of the candidate profile record.
        opportunities_data: A JSON string containing a list of opportunity records.

    Returns:
        A dict with the scored and ranked opportunities.
    """
    try:
        profile = json.loads(profile_data) if isinstance(profile_data, str) else profile_data
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON in profile_data"}

    try:
        opportunities = json.loads(opportunities_data) if isinstance(opportunities_data, str) else opportunities_data
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON in opportunities_data"}

    if isinstance(opportunities, dict):
        opportunities = opportunities.get("records", [opportunities])

    # Get profile keywords for matching
    tech_stack = profile.get("tech_stack", [])
    if isinstance(tech_stack, str):
        try:
            tech_stack = json.loads(tech_stack)
        except json.JSONDecodeError:
            tech_stack = [tech_stack]

    interests = profile.get("interests", [])
    if isinstance(interests, str):
        try:
            interests = json.loads(interests)
        except json.JSONDecodeError:
            interests = [interests]

    preferred_roles = profile.get("preferred_roles", [])
    if isinstance(preferred_roles, str):
        try:
            preferred_roles = json.loads(preferred_roles)
        except json.JSONDecodeError:
            preferred_roles = [preferred_roles]

    search_keywords = profile.get("search_keywords", [])
    if isinstance(search_keywords, str):
        try:
            search_keywords = json.loads(search_keywords)
        except json.JSONDecodeError:
            search_keywords = [search_keywords]

    ranked = []
    for opp in opportunities:
        if not isinstance(opp, dict):
            continue

        score = 0
        match_reasons = []
        opp_text = (
            f"{opp.get('title', '')} {opp.get('description', '')} {opp.get('category', '')}"
        ).lower()

        # Score based on tech stack matches (up to 40 points)
        tech_matches = [t for t in tech_stack if t.lower() in opp_text]
        if tech_matches:
            tech_score = min(40, len(tech_matches) * 10)
            score += tech_score
            match_reasons.append(f"Tech match: {', '.join(tech_matches[:3])}")

        # Score based on role match (up to 25 points)
        role_matches = [r for r in preferred_roles if r.lower() in opp_text]
        if role_matches:
            score += 25
            match_reasons.append(f"Role match: {', '.join(role_matches[:2])}")

        # Score based on interest match (up to 15 points)
        interest_matches = [i for i in interests if i.lower() in opp_text]
        if interest_matches:
            score += min(15, len(interest_matches) * 5)
            match_reasons.append(f"Interest match: {', '.join(interest_matches[:2])}")

        # Score based on category relevance (up to 10 points)
        category = opp.get("category", "")
        category_scores = {
            "job": 10,
            "internship": 9,
            "hackathon": 7,
            "competition": 6,
            "conclave": 5,
        }
        cat_score = category_scores.get(category, 3)
        score += cat_score
        match_reasons.append(f"Category: {category}")

        # Base score for having a deadline (urgency bonus)
        deadline = opp.get("deadline", "")
        if deadline and deadline != "Open":
            score += 5
            match_reasons.append("Has deadline — act soon")

        # Keyword overlap bonus (up to 5 points)
        keyword_hits = sum(1 for kw in search_keywords if kw.lower() in opp_text)
        if keyword_hits:
            score += min(5, keyword_hits * 2)

        # Cap at 100
        score = min(100, score)

        ranked.append({
            "opportunity_id": opp.get("id", 0),
            "title": opp.get("title", ""),
            "url": opp.get("url", ""),
            "category": category,
            "relevance_score": score,
            "match_reasons": match_reasons,
            "profile_id": profile.get("id", 0),
        })

    # Sort by score descending
    ranked.sort(key=lambda x: x["relevance_score"], reverse=True)

    # Assign rank
    for i, item in enumerate(ranked):
        item["rank"] = i + 1

    return {
        "status": "success",
        "total_ranked": len(ranked),
        "ranked_results": ranked,
    }
