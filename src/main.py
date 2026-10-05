#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from graph import OrgGraph
from tools import SurveyTools
from agent import create_agent, AgentState

def main():
    """Main entry point for the survey feedback agent."""

    # Load environment variables
    load_dotenv()

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set. Please set it in .env")
        sys.exit(1)

    # Initialize components
    print("Initializing pipeline...")

    # Paths
    project_root = Path(__file__).parent.parent
    db_path = project_root / "dbt/target/duckdb/main.duckdb"
    employees_path = project_root / "data/employees.csv"
    teams_path = project_root / "data/teams.csv"

    # Check files exist
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        print("Please run 'cd dbt && dbt seed && dbt run' first")
        sys.exit(1)

    if not employees_path.exists() or not teams_path.exists():
        print("ERROR: Seed data files not found")
        sys.exit(1)

    # Build graph and tools
    org_graph = OrgGraph(str(employees_path), str(teams_path))
    tools = SurveyTools(str(db_path), org_graph)
    agent_node = create_agent(tools)

    print("✓ Pipeline initialized")
    print("✓ Database loaded")
    print("✓ Org graph built")
    print("✓ Agent ready\n")

    # Interactive loop
    print("Employee Feedback Intelligence Agent")
    print("=" * 50)
    print("Ask natural language questions about survey data.")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            query = input("Query: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not query:
                continue

            print("\nThinking...\n")

            # Run agent
            state = AgentState()
            state.user_query = query
            state.messages = []

            result = agent_node(state)
            answer = result.get('answer', 'No answer generated')

            print("Agent Response:")
            print("-" * 50)
            print(answer)
            print("-" * 50)
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print()

if __name__ == "__main__":
    main()
