#!/usr/bin/env python3
"""Test script for Graphiti integration.

Run this script to verify Graphiti is working correctly:

    cd backend-python
    pip install -r requirements.txt
    docker-compose up -d  # Start Neo4j
    python scripts/test_graphiti.py

Requirements:
- Neo4j running on localhost:7687
- GOOGLE_API_KEY environment variable set
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


async def main():
    """Run Graphiti integration tests."""
    from graphiti_core import Graphiti
    from graphiti_core.llm_client.google_genai_client import GoogleGenAIClient
    from graphiti_core.embedder.google_genai import GoogleGenAIEmbedder

    # Configuration
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "mindnest123")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not google_api_key:
        print("ERROR: GOOGLE_API_KEY environment variable not set!")
        print("Set it with: export GOOGLE_API_KEY=your-api-key")
        sys.exit(1)

    print("=" * 60)
    print("MindNest Graphiti Integration Test")
    print("=" * 60)
    print(f"Neo4j URI: {neo4j_uri}")
    print(f"Neo4j User: {neo4j_user}")
    print(f"Google API Key: {google_api_key[:10]}...")
    print()

    # Initialize Graphiti
    print("[1/6] Initializing Graphiti...")
    try:
        llm_client = GoogleGenAIClient(
            api_key=google_api_key,
            model="gemini-2.5-flash-lite",
        )
        embedder = GoogleGenAIEmbedder(api_key=google_api_key)

        graphiti = Graphiti(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_password,
            llm_client=llm_client,
            embedder=embedder,
        )
        print("   OK - Graphiti client created")
    except Exception as e:
        print(f"   FAILED: {e}")
        sys.exit(1)

    # Build indices
    print("[2/6] Building indices...")
    try:
        await graphiti.build_indices()
        print("   OK - Indices built")
    except Exception as e:
        print(f"   FAILED: {e}")
        sys.exit(1)

    # Test project ID
    test_project = "test_project_001"

    # Test 1: Add a task
    print("[3/6] Adding task episode...")
    try:
        episode1 = await graphiti.add_episode(
            name="test_task_1",
            episode_body="Buy milk tomorrow, assigned to Petya. Priority: high.",
            source_description="test_user",
            reference_time=datetime.now(),
            group_id=test_project,
        )
        print(f"   OK - Episode created")
        print(f"   Nodes: {len(episode1.nodes) if episode1 and episode1.nodes else 0}")
        print(f"   Edges: {len(episode1.edges) if episode1 and episode1.edges else 0}")
    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Add an expense
    print("[4/6] Adding expense episode...")
    try:
        episode2 = await graphiti.add_episode(
            name="test_expense_1",
            episode_body="Maria paid 500 rubles for dinner. Split between Maria, Petya, and Ivan.",
            source_description="test_user",
            reference_time=datetime.now(),
            group_id=test_project,
        )
        print(f"   OK - Episode created")
        print(f"   Nodes: {len(episode2.nodes) if episode2 and episode2.nodes else 0}")
        print(f"   Edges: {len(episode2.edges) if episode2 and episode2.edges else 0}")
    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Update (edge invalidation)
    print("[5/6] Testing edge invalidation (task completion)...")
    try:
        episode3 = await graphiti.add_episode(
            name="test_update_1",
            episode_body="Petya bought the milk. Task completed.",
            source_description="test_user",
            reference_time=datetime.now(),
            group_id=test_project,
        )
        print(f"   OK - Update episode created")
        print(f"   Nodes: {len(episode3.nodes) if episode3 and episode3.nodes else 0}")
        print(f"   Edges: {len(episode3.edges) if episode3 and episode3.edges else 0}")
    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Test 4: Search
    print("[6/6] Testing search...")
    try:
        results = await graphiti._search(
            query="What tasks does Petya have?",
            group_ids=[test_project],
            num_results=10,
        )
        print(f"   OK - Search completed")
        print(f"   Facts found: {len(results.edges) if results.edges else 0}")
        print(f"   Entities found: {len(results.nodes) if results.nodes else 0}")

        if results.edges:
            print("\n   Sample facts:")
            for edge in results.edges[:3]:
                status = "[EXPIRED]" if edge.expired_at else "[ACTIVE]"
                print(f"   - {status} {edge.fact}")

        if results.nodes:
            print("\n   Sample entities:")
            for node in results.nodes[:3]:
                print(f"   - {node.name}: {node.summary or 'No summary'}")

    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    await graphiti.close()

    print()
    print("=" * 60)
    print("Test completed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Check Neo4j browser at http://localhost:7474")
    print("2. Run: MATCH (n) RETURN n LIMIT 25")
    print("3. Start the API: uvicorn app.main:app --reload")
    print()


if __name__ == "__main__":
    asyncio.run(main())
