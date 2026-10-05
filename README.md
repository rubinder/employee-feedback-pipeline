# Employee Feedback Intelligence Pipeline

A demonstration project showcasing a modern data + ML stack for analyzing employee engagement.

**Features:**
- ✓ Synthetic survey data pipeline (dbt + DuckDB)
- ✓ Organizational hierarchy and network analysis (NetworkX)
- ✓ Natural language AI agent (LangGraph + Claude)
- ✓ Semantic layer with defined metrics
- ✓ Local-first, no infrastructure required

**Stack:** Python • dbt • DuckDB • NetworkX • LangGraph • Anthropic API

---

## Quick Start

### Requirements
- Python 3.11+
- `pip install -r requirements.txt`
- `ANTHROPIC_API_KEY` environment variable

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Run dbt pipeline
cd dbt
dbt seed     # Load seed data into DuckDB
dbt run      # Transform data with models
dbt test     # Run data quality tests
cd ..

# 4. Start the agent
python src/main.py
```

### Example Queries

```
> Query: Which teams have declining engagement over the last two quarters?

Agent Response:
Engineering shows a declining trend with satisfaction dropping 5.4% from Q3 to Q4. 
This correlates with increased feature development velocity and known bandwidth challenges. 
Product team shows improvement, likely due to successful Q3 launch reducing context-switching.
...

> Query: Show me the org structure for the Finance team

Agent Response:
Finance team has 2 members reporting to Leo Jackson (Finance Manager):
- Leo Jackson (Manager)
- Noah Anderson (IC)

Team sentiment: 78% positive, 22% neutral. Satisfaction stable at 3.8/5.
```

---

## Architecture

### System Overview

```
User Query (Natural Language)
    ↓
[LangGraph Agent] ← reasons, calls tools
    ↓
[Tools Layer] ← query metrics, org context, trend analysis
    ↓
    ├─ DuckDB Database (analytics tables)
    │  ├─ fct_survey_metrics (satisfaction by team/quarter)
    │  └─ dim_org_structure (org hierarchy)
    │
    └─ NetworkX Org Graph (in-memory)
       ├─ Employee nodes
       ├─ Manager→Employee edges (reporting)
       └─ Employee↔Employee edges (peers)
    ↓
[dbt Transformation Layer]
    ├─ stg_employees (clean employee data)
    ├─ stg_survey_responses (parsed survey data)
    ├─ fct_survey_metrics (aggregations)
    └─ dim_org_structure (denormalization)
    ↓
[Raw Seed Data]
    ├─ employees.csv
    ├─ survey_responses.csv
    └─ teams.csv
```

### Layer Responsibilities

| Layer | Role |
|-------|------|
| **Data Ingestion** | Load seed CSVs into DuckDB via dbt seeds |
| **Transformation** | dbt models: clean, aggregate, denormalize |
| **Semantic Layer** | Defined metrics (satisfaction, response rate, sentiment) |
| **Org Graph** | NetworkX: employee relationships, network queries |
| **Agent** | LangGraph + Claude: natural language interface |

---

## Data Model

### Fact Table: fct_survey_metrics
```
Quarter      | Team        | Response_Count | Avg_Satisfaction | Pct_Positive
Q1-2024      | Engineering | 3              | 4.2              | 66.7%
Q1-2024      | Product     | 3              | 3.9              | 60.0%
Q2-2024      | Engineering | 3              | 4.1              | 66.7%
...
```

### Dimension Table: dim_org_structure
```
Employee_ID | Employee_Name | Team        | Manager_Name
1           | Alice Johnson | Engineering | NULL (CEO-level)
2           | Bob Smith     | Engineering | Alice Johnson
4           | Diana Wilson  | Product     | NULL
...
```

### Org Graph Structure
```
Nodes: Employees (with team attribute)

Edges:
  Alice Johnson --manages--> Bob Smith      (reporting)
  Alice Johnson <--peer--> Grace Lee        (same team)
  Diana Wilson --manages--> Eve Martinez    (reporting)
```

---

## Project Structure

```
employee_feedback_pipeline/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # Template for .env
│
├── data/
│   ├── employees.csv                  # 15 employees, 6 teams
│   ├── survey_responses.csv           # 4 quarters of feedback
│   └── teams.csv                      # 6 teams
│
├── dbt/
│   ├── dbt_project.yml                # dbt configuration
│   ├── models/
│   │   ├── stg_employees.sql          # Clean employee data
│   │   ├── stg_survey_responses.sql   # Parse survey responses
│   │   ├── fct_survey_metrics.sql     # Aggregate metrics
│   │   ├── dim_org_structure.sql      # Org hierarchy
│   │   └── schema.yml                 # Source definitions + tests
│   ├── tests/
│   │   ├── test_satisfaction_range.sql
│   │   └── test_employee_ids.sql
│   └── target/
│       └── duckdb/main.duckdb         # Generated database
│
├── src/
│   ├── graph.py                       # NetworkX org graph
│   ├── tools.py                       # Agent tools (4 functions)
│   ├── agent.py                       # LangGraph agent
│   └── main.py                        # CLI entry point
│
└── docs/superpowers/
    ├── specs/                         # Design specification
    └── plans/                         # Implementation plan
```

---

## Agent Tools

The agent has access to 4 tools:

### 1. `query_team_metrics(team_name, quarters)`
Fetch satisfaction metrics for a team across specified quarters.

**Returns:** Satisfaction score, response count, sentiment distribution

### 2. `compare_quarters(team_name, quarters)`
Analyze trends across quarters to detect improving/declining/stable patterns.

**Returns:** Trend direction, percent change, first/last scores

### 3. `org_context(team_name)`
Get team structure and member information.

**Returns:** Team members, manager names, org hierarchy

### 4. `get_manager_and_team(name)`
Get org information for a specific employee.

**Returns:** Manager name, team, direct reports, org level

---

## Testing

### dbt Data Quality Tests

```bash
cd dbt
dbt test
```

Tests include:
- Satisfaction scores in valid range [1, 5]
- Non-null employee IDs
- Unique response IDs

### Manual Agent Testing

Example questions to try:

```
1. "Which teams have declining engagement over the last two quarters?"
2. "Show me satisfaction trends for the Product team"
3. "What's the org structure for the Engineering team?"
4. "Are Sales and Engineering teams connected?"
5. "Which manager has the most engaged team?"
```

---

## Design Decisions

### Why DuckDB?
- File-based, serverless database
- Zero infrastructure setup (perfect for portfolio demo)
- Fast analytical queries
- Ships with Python via `dbt-duckdb`

### Why NetworkX?
- Python-native graph library
- In-memory storage (no extra DB)
- Simple API for relationship queries
- Easy to visualize and extend

### Why LangGraph?
- Modern agentic pattern (vs monolithic prompting)
- Built for multi-step reasoning with tools
- Integrates cleanly with Claude API
- Transparent tool execution flow

### Why dbt?
- Demonstrates knowledge of semantic layer
- SQL-based transformations are readable
- Tests + documentation built-in
- Production-grade data transformation practice

---

## Extending This Project

**Add new metrics:**
```sql
-- Add new dbt model in dbt/models/
select
  team,
  quarter,
  count(distinct employee_id) as team_size,
  -- ... more aggregations
from stg_survey_responses
group by team, quarter
```

**Add new agent tools:**
```python
# In src/tools.py
def your_new_tool(self, param1: str) -> Dict:
    """Query or compute something."""
    result = ...
    return result

# In src/agent.py, add to tool_definitions
{
    "name": "your_new_tool",
    "description": "...",
    "input_schema": {...}
}
```

**Add graph analysis:**
```python
# In src/graph.py
def find_collaboration_clusters(self):
    """Find groups of employees who mention each other."""
    ...
```

---

## Notes for Interviewers

This project demonstrates:

1. **Data pipeline design** — End-to-end from ingestion to queries
2. **Semantic layer** — dbt models, metrics definitions, naming standards
3. **Graph structures** — Org networks, relationship traversal
4. **Agentic AI** — Multi-step reasoning with tools, Claude API integration
5. **Software engineering** — Clean code, testability, documentation

The demo intentionally keeps scope bounded (50 employees, 4 quarters, 6 teams) to show something **complete and working** rather than a partial implementation of a larger system.

---

## License

MIT — See LICENSE file

---

**Built by:** Claude Haiku 4.5  
**Last Updated:** 2026-10-05
