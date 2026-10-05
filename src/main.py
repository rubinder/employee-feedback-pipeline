#!/usr/bin/env python3
import os
import sys
import logging
import time
from pathlib import Path
# Load .env manually to handle subprocess context
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from graph import OrgGraph
from tools import SurveyTools
from agent import create_agent, AgentState

# Configure logging
log_file = Path(__file__).parent.parent / "agent_runs.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the survey feedback agent."""

    logger.info("=" * 60)
    logger.info("Employee Feedback Intelligence Agent Started")
    logger.info("=" * 60)

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set. Please set it in .env")
        print("ERROR: ANTHROPIC_API_KEY not set. Please set it in .env")
        sys.exit(1)

    # Initialize components
    logger.info("Initializing pipeline...")
    print("Initializing pipeline...")

    # Paths
    project_root = Path(__file__).parent.parent
    db_path = project_root / "dbt/target/duckdb/main.duckdb"
    employees_path = project_root / "data/employees.csv"
    teams_path = project_root / "data/teams.csv"

    # Check files exist
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        print(f"ERROR: Database not found at {db_path}")
        print("Please run 'cd dbt && dbt seed && dbt run' first")
        sys.exit(1)

    if not employees_path.exists() or not teams_path.exists():
        logger.error("Seed data files not found")
        print("ERROR: Seed data files not found")
        sys.exit(1)

    # Build graph and tools
    logger.info("Building org graph...")
    org_graph = OrgGraph(str(employees_path), str(teams_path))
    logger.info(f"Graph built: {org_graph.graph.number_of_nodes()} nodes, {org_graph.graph.number_of_edges()} edges")

    logger.info("Connecting to DuckDB...")
    tools = SurveyTools(str(db_path), org_graph)
    logger.info("Database connected and tools initialized")

    logger.info("Creating LangGraph agent...")
    agent_node = create_agent(tools)
    logger.info("Agent ready for queries")

    print("✓ Pipeline initialized")
    print("✓ Database loaded")
    print("✓ Org graph built")
    print("✓ Agent ready\n")

    # Interactive loop
    print("Employee Feedback Intelligence Agent")
    print("=" * 50)
    print("Ask natural language questions about survey data.")
    print("Type 'quit' to exit.\n")

    query_count = 0
    start_time = time.time()

    while True:
        try:
            query = input("Query: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                logger.info("Session ended by user")
                print("Goodbye!")
                break

            if not query:
                continue

            query_count += 1
            logger.info(f"\n--- Query #{query_count} ---")
            logger.info(f"User Query: {query}")

            print("\nThinking...\n")

            # Run agent
            query_start = time.time()
            state = AgentState()
            state.user_query = query
            state.messages = []

            result = agent_node(state)
            answer = result.get('answer', 'No answer generated')
            query_duration = time.time() - query_start

            logger.info(f"Agent Response (completed in {query_duration:.2f}s):")
            logger.info(answer)

            print("Agent Response:")
            print("-" * 50)
            print(answer)
            print("-" * 50)
            print()

        except KeyboardInterrupt:
            logger.info("Session interrupted by user")
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error during query: {e}", exc_info=True)
            print(f"Error: {e}")
            print()

    # Session summary
    total_duration = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"Session Summary: {query_count} queries in {total_duration:.2f}s")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
