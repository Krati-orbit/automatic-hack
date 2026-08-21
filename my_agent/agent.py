from google.adk.agents.llm_agent import Agent

# ── Import all tools ─────────────────────────────────────────────────────────
from .tools.db_tools import store_to_db, read_from_db
from .tools.resume_tools import extract_resume
from .tools.analysis_tools import analyze_resume
from .tools.profile_tools import make_profile
from .tools.search_tools import search_web
from .tools.ranking_tools import rank_results

MODEL = "gemini-3.1-flash-lite"

# ── Stage 1: Resume Extractor ────────────────────────────────────────────────
resume_extractor = Agent(
    model=MODEL,
    name="resume_extractor",
    description="Extracts structured information from an uploaded resume and stores it in the database. Call this agent with the full resume text.",
    instruction="""You are the Resume Extractor agent. When you receive resume text:

1. Call the `extract_resume` tool with the full resume text to parse it into structured fields.
2. Call the `store_to_db` tool with table='resumes' and the extracted data as a JSON string to save it.
3. Return the stored resume ID and a brief confirmation.

Always complete both steps — extract then store.""",
    tools=[extract_resume, store_to_db],
    mode="single_turn",
)

# ── Stage 2: Resume Analyzer ─────────────────────────────────────────────────
resume_analyzer = Agent(
    model=MODEL,
    name="resume_analyzer",
    description="Analyzes stored resume data to identify strengths, weaknesses, experience level, and domain focus. Call this agent after resume extraction is complete.",
    instruction="""You are the Resume Analyzer agent. When activated:

1. Call `read_from_db` with table='resumes' to fetch the latest resume record.
2. Call `analyze_resume` with the resume data (as a JSON string) to generate analysis.
3. Call `store_to_db` with table='resume_analysis' and include the resume_id from step 1, along with the analysis fields.
4. Return a brief summary of the analysis.

Always complete all three steps — read, analyze, then store.""",
    tools=[read_from_db, analyze_resume, store_to_db],
    mode="single_turn",
)

# ── Stage 3: Profile Maker ───────────────────────────────────────────────────
profile_maker = Agent(
    model=MODEL,
    name="profile_maker",
    description="Builds a structured candidate profile from resume and analysis data including tech stack, interests, and career goals. Call this agent after resume analysis is complete.",
    instruction="""You are the Profile Maker agent. When activated:

1. Call `read_from_db` with table='resumes' to fetch the resume data.
2. Call `read_from_db` with table='resume_analysis' to fetch the analysis data.
3. Call `make_profile` with both the resume data and analysis data as JSON strings.
4. Call `store_to_db` with table='profiles' and include the resume_id, along with the profile fields.
5. Return a brief summary of the profile.

Always complete all steps — read resume, read analysis, make profile, then store.""",
    tools=[read_from_db, make_profile, store_to_db],
    mode="single_turn",
)

# ── Stage 4: Opportunity Scout ────────────────────────────────────────────────
opportunity_scout = Agent(
    model=MODEL,
    name="opportunity_scout",
    description="Searches the internet for jobs, internships, competitions, hackathons, and conclaves matching the candidate profile. Call this agent after profile is built.",
    instruction="""You are the Opportunity Scout agent. When activated:

1. Call `read_from_db` with table='profiles' to fetch the candidate profile.
2. Use the search_keywords from the profile to make multiple `search_web` calls.
   For each keyword, search across different categories: 'job', 'internship', 'competition', 'hackathon', 'conclave'.
   Do at least 3-5 searches covering different categories.
3. For each batch of results, call `store_to_db` with table='opportunities' to save each opportunity. Include the profile_id.
4. Return how many opportunities were found.

Be thorough — search across multiple categories to find diverse opportunities.""",
    tools=[read_from_db, search_web, store_to_db],
    mode="single_turn",
)

# ── Stage 5: Opportunity Ranker ───────────────────────────────────────────────
opportunity_ranker = Agent(
    model=MODEL,
    name="opportunity_ranker",
    description="Ranks and organizes found opportunities by relevance to the candidate, scoring them 0-100. Call this agent after opportunity search is complete.",
    instruction="""You are the Opportunity Ranker agent. When activated:

1. Call `read_from_db` with table='profiles' to fetch the candidate profile.
2. Call `read_from_db` with table='opportunities' to fetch all raw opportunities.
3. Call `rank_results` with the profile data and opportunities data as JSON strings.
4. For each ranked result, call `store_to_db` with table='ranked_opportunities' to save it.
5. Return the top ranked opportunities showing rank, title, category, score, and match reasons.

Always complete all steps — read, rank, store, then present.""",
    tools=[read_from_db, rank_results, store_to_db],
    mode="single_turn",
)

# ── Coordinator Root Agent ────────────────────────────────────────────────────
root_agent = Agent(
    model=MODEL,
    name="root_agent",
    description="CareerOS coordinator — orchestrates the full resume-to-opportunities pipeline.",
    instruction="""You are the CareerOS coordinator agent. You manage a sequential pipeline of specialized sub-agents.

When a user uploads or pastes their resume, you MUST run the full pipeline by calling each sub-agent in order:

1. Call `resume_extractor` with the full resume text to extract and store the resume.
2. Call `resume_analyzer` to analyze the stored resume data.
3. Call `profile_maker` to build a structured candidate profile.
4. Call `opportunity_scout` to search for matching opportunities.
5. Call `opportunity_ranker` to rank and organize the results.

Call them ONE AT A TIME in this exact sequence. Wait for each to complete before calling the next.

After ALL five stages complete, present a final summary to the user showing:
- Their extracted profile highlights
- The top ranked opportunities with scores

If the user asks a general question (not providing a resume), answer it directly without triggering the pipeline.""",
    sub_agents=[resume_extractor, resume_analyzer, profile_maker, opportunity_scout, opportunity_ranker],
)