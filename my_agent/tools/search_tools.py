"""Web search tool for CareerOS — opportunity discovery."""

import json
import hashlib


def search_web(query: str, category: str) -> dict:
    """Searches the internet for opportunities matching the query.

    Looks for jobs, internships, competitions, hackathons, and conclaves
    related to the candidate's profile and skills.

    Args:
        query: The search query string (e.g. 'React developer internship').
        category: The type of opportunity to search for.
                  One of: 'job', 'internship', 'competition', 'hackathon', 'conclave'.

    Returns:
        A dict with a list of matching opportunities.
    """
    # Generate deterministic but varied mock results based on query
    query_hash = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)

    # Mock data pools per category
    mock_sources = {
        "job": {
            "sources": ["LinkedIn", "Indeed", "Glassdoor", "AngelList", "Wellfound"],
            "title_templates": [
                "{keyword} Developer - Remote",
                "Junior {keyword} Engineer",
                "{keyword} Software Engineer - Startup",
                "Associate {keyword} Developer",
                "{keyword} Engineer - Full Time",
            ],
        },
        "internship": {
            "sources": ["LinkedIn", "Internshala", "AngelList", "Company Careers"],
            "title_templates": [
                "{keyword} Intern - Summer 2026",
                "{keyword} Development Internship",
                "Remote {keyword} Intern",
                "{keyword} Engineering Internship (Paid)",
            ],
        },
        "competition": {
            "sources": ["Devpost", "HackerEarth", "Kaggle", "MLH"],
            "title_templates": [
                "{keyword} Code Challenge 2026",
                "Global {keyword} Competition",
                "{keyword} Innovation Challenge",
                "{keyword} Coding Contest",
            ],
        },
        "hackathon": {
            "sources": ["Devpost", "MLH", "HackerEarth", "Unstop"],
            "title_templates": [
                "{keyword} Hackathon 2026",
                "Build with {keyword} - 48hr Hackathon",
                "{keyword} HackFest Global",
                "Open {keyword} Hack",
            ],
        },
        "conclave": {
            "sources": ["Eventbrite", "Meetup", "Conference Alerts", "Tech Events"],
            "title_templates": [
                "{keyword} Tech Summit 2026",
                "Global {keyword} Conference",
                "{keyword} Developer Conclave",
                "{keyword} Innovation Summit",
            ],
        },
    }

    cat_data = mock_sources.get(category, mock_sources["job"])
    keyword = query.split()[0] if query else "Tech"

    results = []
    num_results = 3 + (query_hash % 3)  # 3-5 results per search

    for i in range(min(num_results, len(cat_data["title_templates"]))):
        title = cat_data["title_templates"][i].format(keyword=keyword)
        source = cat_data["sources"][i % len(cat_data["sources"])]

        # Generate a mock URL
        slug = title.lower().replace(" ", "-").replace("---", "-")
        url = f"https://{source.lower().replace(' ', '')}.com/opportunity/{slug}"

        results.append({
            "title": title,
            "url": url,
            "description": f"Exciting {category} opportunity: {title}. Looking for candidates with {query} skills.",
            "source": source,
            "category": category,
            "deadline": "2026-09-30" if category in ["competition", "hackathon"] else "Open",
        })

    return {
        "status": "success",
        "query": query,
        "category": category,
        "count": len(results),
        "results": results,
    }
