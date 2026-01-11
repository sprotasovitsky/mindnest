#!/usr/bin/env python3
"""Test script for Graphiti integration.

Run this script to verify Graphiti is working correctly:

    cd backend-python
    pip install -r requirements.txt
    docker-compose up -d  # Start Neo4j
    python scripts/test_graphiti.py

Requirements:
- Neo4j running on localhost:7687
- Vertex AI credentials configured in .env
"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


async def main():
    """Run Graphiti integration tests."""
    from app.config import get_settings
    from app.graphiti_client import get_knowledge_graph, close_knowledge_graph

    settings = get_settings()

    if not settings.gcp_service_account_email or not settings.gcp_private_key:
        print("ERROR: Vertex AI credentials not set!")
        print("Set GCP_SERVICE_ACCOUNT_EMAIL and GCP_PRIVATE_KEY in .env")
        sys.exit(1)

    print("=" * 60)
    print("MindNest Graphiti Integration Test")
    print("=" * 60)
    print(f"Neo4j URI: {settings.neo4j_uri}")
    print(f"Vertex AI Project: {settings.vertex_ai_project_id}")
    print(f"Service Account: {settings.gcp_service_account_email}")
    print()

    # Test project ID
    test_project = "test_project_001"

    # Initialize Graphiti via app's client
    print("[1/6] Initializing Graphiti...")
    try:
        kg = await get_knowledge_graph()
        print("   OK - Graphiti client created")
    except Exception as e:
        print(f"   FAILED: {e}")
        sys.exit(1)

    # Test 1: Add a task
    print("[2/6] Adding task episode...")
    try:
        episode1 = await kg._client.add_episode(
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
    print("[3/6] Adding expense episode...")
    try:
        episode2 = await kg._client.add_episode(
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
    print("[4/6] Testing edge invalidation (task completion)...")
    try:
        episode3 = await kg._client.add_episode(
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
    print("[5/6] Testing search...")
    try:
        results = await kg.search(
            query="What tasks does Petya have?",
            project_id=test_project,
        )
        print(f"   OK - Search completed")
        print(f"   Facts found: {len(results.get('edges', []))}")
        print(f"   Entities found: {len(results.get('nodes', []))}")

        if results.get('edges'):
            print("\n   Sample facts:")
            for edge in results['edges'][:3]:
                status = "[EXPIRED]" if edge.get('expired_at') else "[ACTIVE]"
                print(f"   - {status} {edge.get('fact')}")

    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Test 5: LLM generation
    print("[6/6] Testing LLM generation...")
    try:
        from app.llm import generate_text
        response = await generate_text("Say hello in one word", model=settings.llm_model_pro)
        print(f"   OK - LLM response: {response[:50]}")
    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    await close_knowledge_graph()

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
