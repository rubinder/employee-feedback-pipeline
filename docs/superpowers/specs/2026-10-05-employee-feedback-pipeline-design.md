# Employee Feedback Intelligence Pipeline — Design Spec

**Date:** 2026-10-05  
**Project Type:** Demonstration/Portfolio Project  
**Audience:** Hiring/interview showcase  
**Goal:** Build a complete, polished end-to-end demo of a modern data + ML stack

---

## Overview

A synthetic survey data pipeline that demonstrates:
- **Data transformation** (dbt models, semantic layer)
- **Network analysis** (org graph with NetworkX)
- **AI-powered querying** (LangGraph agent with Claude)

Interviewers can run the project locally and ask the agent natural-language questions like "Which teams have declining engagement over the last two quarters?" and get data-backed answers.

---

## Architecture

### Three-Layer System

```
User Query
    ↓
[LangGraph Agent] — reasons over data, calls tools
    ↓
[Tools Layer] — Query metrics, org context, trend comparison
    ↓
[Data Layer]
├── DuckDB: fct_survey_metrics, dim_org_structure (from dbt)
└── NetworkX: org_graph (employees, teams, manager/peer edges)
    ↓
[dbt Transformation] — ingestion, metrics, denormalization
    ↓
[Seed Data] — employees.csv, survey_responses.csv, teams.csv
```

### Component Overview

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Data Storage** | DuckDB (file-based) | Fast, serverless analytics DB; no infrastructure setup |
| **Transformation** | dbt | Semantic layer, metrics definitions, data quality tests |
| **Org Graph** | NetworkX | Employee/team relationships, network queries |
| **Agent** | LangGraph + Claude | Natural language interface to data and graph |

---

## Data Pipeline

### Synthetic Seed Data

Pre-generated CSVs (~50 employees, 5-6 teams, 4 quarters of responses):

**`employees.csv`**
- id, name, team, manager_id, start_date

**`survey_responses.csv`**
- response_id, employee_id, quarter, satisfaction_score (1-5), sentiment_label (positive/neutral/negative), comment

**`teams.csv`**
- team_id, team_name, department

### dbt Models

Located in `dbt/models/`:

1. **`stg_employees.sql`** — Load and clean employee data; join with team information
2. **`stg_survey_responses.sql`** — Parse survey responses; assign sentiment labels; link to employees
3. **`fct_survey_metrics.sql`** — Aggregate metrics:
   - Satisfaction score by team and quarter
   - Response rate by team
   - Sentiment distribution (% positive/neutral/negative)
4. **`dim_org_structure.sql`** — Denormalized org hierarchy for graph construction (manager chains, peer networks)

### Data Quality

Light dbt testing:
- Non-null checks on employee_id, satisfaction_score
- Satisfaction score in valid range [1, 5]
- Unique employee IDs

### Output

DuckDB database (`dbt/target/duckdb/main.duckdb`) with fact/dimension tables ready for agent queries.

---

## Org Graph (NetworkX)

### Structure

**Nodes:**
- Employee nodes: attributes include id, name, team, department

**Edges:**
- **Manager → Employee** (directed): reporting structure
- **Employee ↔ Employee** (undirected): peers in the same team
- **Team ↔ Team** (directed): cross-team collaboration (derived from survey comments)

### Construction

Python script loads `dim_org_structure` and seed CSVs, builds NetworkX DiGraph in memory at startup (~100 lines).

### Use Cases

- Manager-level queries: "Show me engagement trends for [manager]'s team"
- Peer network queries: "Are these two teams connected?"
- Collaboration analysis: "Which teams collaborate most based on survey feedback?"

---

## LangGraph Agent

### Tools (4 total)

1. **`query_team_metrics(team_name: str, quarters: list[str]) → dict`**
   - Returns: satisfaction_score, response_rate, sentiment_breakdown for given team(s)
   - Used for: fetching raw metrics for a team

2. **`get_manager_and_team(name: str) → dict`**
   - Returns: team, manager, direct reports, org_level
   - Used for: org structure lookups

3. **`compare_quarters(team_name: str, quarters: list[str]) → dict`**
   - Returns: trend (improving/declining/stable), pct_change, key_drivers
   - Used for: multi-quarter trend analysis

4. **`org_context(team_name: str) → dict`**
   - Returns: peer_teams, cross_team_mentions, collaboration_patterns
   - Used for: contextualizing metrics with org relationships

### Workflow

**Example user query:** "Which teams have declining engagement over the last two quarters?"

1. Agent reasons: I need to find engagement trends for multiple teams
2. Calls `compare_quarters()` for each team → identifies declining teams
3. Calls `query_team_metrics()` for context → gets satisfaction scores, response rates
4. Calls `org_context()` for context → finds related teams, notes collaborations
5. Claude synthesizes: "Engineering has a 15% drop in satisfaction; may be related to Q3 product launch impacting product team (which Engineering collaborates with heavily)"

### No Persistence

Each query is independent. No chat history or memory needed for the demo.

---

## Project Structure

```
employee_feedback_pipeline/
├── README.md                          # Architecture diagram, data model, screenshots
├── data/
│   ├── employees.csv
│   ├── survey_responses.csv
│   └── teams.csv
├── dbt/
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── stg_employees.sql
│   │   ├── stg_survey_responses.sql
│   │   ├── fct_survey_metrics.sql
│   │   └── dim_org_structure.sql
│   ├── tests/
│   │   └── [dbt test files]
│   └── target/                        # Generated DuckDB database
├── src/
│   ├── graph.py                       # NetworkX org graph builder
│   ├── agent.py                       # LangGraph agent definition
│   ├── tools.py                       # Tool implementations
│   └── main.py                        # Entry point; CLI for queries
├── requirements.txt
├── .env.example
└── screenshots/                       # Demo run screenshots
    ├── dbt_run.png
    ├── agent_query_1.png
    └── agent_query_2.png
```

---

## Demo Flow

**Setup (first run):**
```
pip install -r requirements.txt
cp .env.example .env
# Set ANTHROPIC_API_KEY in .env
python src/main.py
```

**Usage:**
```
> Query: Which teams have declining engagement over the last two quarters?
> Agent: [runs tools, synthesizes answer with data + org context]

> Query: Show me satisfaction trends for the Engineering team
> Agent: [returns time series, highlights patterns]
```

**README includes:**
- System architecture diagram (3-layer visual)
- Data model / ERD
- 2-3 screenshots of working demo
- Quick-start instructions

---

## Testing

- **dbt tests:** Data quality checks in dbt/tests/ (non-null, range validation)
- **Agent testing:** Manual queries during demo (not unit tests for portfolio scope)
- **Graph validation:** Quick check that graph loads, nodes/edges are correct (optional test script)

---

## Success Criteria

✓ Full pipeline runs end-to-end locally without infrastructure setup  
✓ Agent responds to natural language queries with meaningful answers  
✓ README includes architecture diagram, data model, and screenshots  
✓ Code is clean and well-structured (hiring portfolio standard)  
✓ Demo can be shown in 5 minutes and understood by someone unfamiliar with the codebase  

---

## Tech Stack Summary

| Component | Technology | Why |
|-----------|-----------|-----|
| Data storage | DuckDB | File-based, zero setup, fast analytics |
| Transformation | dbt | Show semantic layer + best practices |
| Graph | NetworkX | Python-native, simple, in-memory |
| Agent | LangGraph | Modern agentic pattern, integrates with Claude |
| LLM | Claude (Anthropic API) | Reasoning over structured data |

---

## Deployment & Sharing

- **Local-first:** Designed to run entirely locally (no cloud infra for the demo)
- **GitHub:** Public repo with clear README for portfolio/interview sharing
- **Reproducibility:** Seed data included; requires only Python + ANTHROPIC_API_KEY
