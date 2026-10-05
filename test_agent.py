#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
load_dotenv()

from graph import OrgGraph
from tools import SurveyTools
from agent import create_agent, AgentState

print("🚀 Testing Employee Feedback Intelligence Agent\n")
print("=" * 60)

print("\n1. Building org graph...")
g = OrgGraph('data/employees.csv', 'data/teams.csv')
print(f"   ✓ Graph: {g.graph.number_of_nodes()} nodes, {g.graph.number_of_edges()} edges")

print("\n2. Connecting to database...")
tools = SurveyTools('dbt/target/duckdb/main.duckdb', g)
print("   ✓ Database connected")

print("\n3. Creating agent...")
agent = create_agent(tools)
print("   ✓ Agent ready")

print("\n" + "=" * 60)
print("Sample Query: Which teams have declining engagement over the last two quarters?")
print("=" * 60 + "\n")

state = AgentState()
state.user_query = "Which teams have declining engagement over the last two quarters?"
state.messages = []

print("Agent is thinking...\n")
result = agent(state)
answer = result.get('answer', 'No response')

print("Agent Response:")
print("-" * 60)
print(answer)
print("-" * 60)

print("\n✅ Test complete. Check agent_runs.log for full execution log.")
