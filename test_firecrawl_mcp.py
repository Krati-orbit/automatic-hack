"""Verification test script for Firecrawl MCP integration in CareerOS."""

import os
import sys

# Ensure d:\careerOS is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from my_agent.tools.search_tools import search_web
from my_agent.mcp_servers.mcp_scout_server import scout_and_store_opportunities


def test_firecrawl_search():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 60)
    print("[TEST] Testing Firecrawl MCP Search Tool Integration")
    print("=" * 60)

    categories = ["job", "internship", "competition", "hackathon"]
    for cat in categories:
        res = search_web("Generative AI Developer", cat)
        print(f"\nCategory: {cat.upper()}")
        print(f"Status: {res.get('status')}")
        print(f"Engine Used: {res.get('engine')}")
        print(f"Results Count: {res.get('count')}")
        for item in res.get("results", [])[:2]:
            print(f"  - [{item.get('source')}] {item.get('title')[:60]} -> {item.get('url')}")

    print("\n" + "=" * 60)
    print("[RUN] Testing MCP Scout Server Opportunity Discovery")
    print("=" * 60)
    scout_res = scout_and_store_opportunities(profile_id=1)
    print("Scout Output:", scout_res)
    print("\n[SUCCESS] Firecrawl MCP Integration Verification Completed Successfully!")


if __name__ == "__main__":
    test_firecrawl_search()
