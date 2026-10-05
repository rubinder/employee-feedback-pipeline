import json
from typing import Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from anthropic import Anthropic

client = Anthropic()

class AgentState:
    """Simple state container for agent."""
    def __init__(self):
        self.messages = []
        self.user_query = ""

def create_agent(tools_instance):
    """Create a LangGraph agent with survey tools."""

    def format_tool_response(tool_name: str, result: dict) -> str:
        """Format tool response as a string."""
        if 'error' in result:
            return f"Error from {tool_name}: {result['error']}"
        return json.dumps(result, indent=2)

    def agent_node(state):
        """Agent reasoning node."""
        # Build messages for Claude
        system_prompt = """You are an AI assistant helping answer questions about employee engagement and satisfaction.
You have access to survey data, org structure, and trend analysis tools.

When answering questions:
1. Use the tools to gather data
2. Synthesize answers using both metrics and org context
3. Explain patterns and trends clearly

Available tools:
- query_team_metrics(team_name, quarters): Get satisfaction metrics for a team
- compare_quarters(team_name, quarters): Analyze trends across quarters
- org_context(team_name): Get team structure and members
- get_manager_and_team(name): Get org info for an employee

Respond with clear, data-backed answers."""

        messages = state.messages + [{"role": "user", "content": state.user_query}]

        # First call to Claude with tool definitions
        tool_definitions = [
            {
                "name": "query_team_metrics",
                "description": "Query satisfaction metrics for a team",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "team_name": {"type": "string"},
                        "quarters": {"type": "array", "items": {"type": "string"}, "nullable": True}
                    },
                    "required": ["team_name"]
                }
            },
            {
                "name": "compare_quarters",
                "description": "Compare metrics across quarters to find trends",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "team_name": {"type": "string"},
                        "quarters": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["team_name", "quarters"]
                }
            },
            {
                "name": "org_context",
                "description": "Get org structure and team context",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "team_name": {"type": "string"}
                    },
                    "required": ["team_name"]
                }
            },
            {
                "name": "get_manager_and_team",
                "description": "Get manager and team info for an employee",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    },
                    "required": ["name"]
                }
            }
        ]

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            tools=tool_definitions,
            messages=messages
        )

        # Process response and handle tool calls
        if response.stop_reason == "tool_use":
            # Extract tool calls from response
            tool_calls = [block for block in response.content if block.type == "tool_use"]

            # Execute tools and build follow-up
            state.messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.name
                tool_input = tool_call.input

                # Execute the tool
                if tool_name == "query_team_metrics":
                    result = tools_instance.query_team_metrics(
                        tool_input.get("team_name"),
                        tool_input.get("quarters")
                    )
                elif tool_name == "compare_quarters":
                    result = tools_instance.compare_quarters(
                        tool_input.get("team_name"),
                        tool_input.get("quarters")
                    )
                elif tool_name == "org_context":
                    result = tools_instance.org_context(tool_input.get("team_name"))
                elif tool_name == "get_manager_and_team":
                    result = tools_instance.get_manager_and_team(tool_input.get("name"))
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": format_tool_response(tool_name, result)
                })

            state.messages.append({"role": "user", "content": tool_results})

            # Second call to get final response
            final_response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=system_prompt,
                messages=state.messages
            )

            answer = next(
                (block.text for block in final_response.content if hasattr(block, 'text')),
                "No response generated"
            )
        else:
            # Direct response without tools
            answer = next(
                (block.text for block in response.content if hasattr(block, 'text')),
                "No response generated"
            )

        return {"answer": answer}

    return agent_node
