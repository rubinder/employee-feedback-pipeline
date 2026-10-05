#!/usr/bin/env python3
"""
Setup script to create DuckDB database with staging and fact/dimension models
This accomplishes what dbt seed and dbt run would do.
"""

import duckdb
import os
import csv
from pathlib import Path

# Create database connection
db_path = "dbt/target/duckdb/main.duckdb"
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = duckdb.connect(db_path)

# Create schemas
conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
conn.execute("CREATE SCHEMA IF NOT EXISTS analytics")

# Drop existing tables to start fresh
conn.execute("DROP TABLE IF EXISTS analytics.dim_org_structure")
conn.execute("DROP TABLE IF EXISTS analytics.fct_survey_metrics")
conn.execute("DROP TABLE IF EXISTS analytics.stg_survey_responses")
conn.execute("DROP TABLE IF EXISTS analytics.stg_employees")
conn.execute("DROP TABLE IF EXISTS raw.employees")
conn.execute("DROP TABLE IF EXISTS raw.survey_responses")
conn.execute("DROP TABLE IF EXISTS raw.teams")

print("✓ Schemas created")

# Load seed data from CSVs
data_dir = Path("data")

# Load employees with proper null handling
conn.execute(f"""
    CREATE TABLE IF NOT EXISTS raw.employees AS
    SELECT
        id,
        name,
        team,
        CASE WHEN manager_id = 'NULL' THEN NULL ELSE CAST(manager_id AS INTEGER) END as manager_id,
        start_date
    FROM read_csv_auto('{data_dir}/employees.csv')
""")
print("✓ Loaded employees.csv into raw.employees")

# Load survey_responses
conn.execute(f"""
    CREATE TABLE IF NOT EXISTS raw.survey_responses AS
    SELECT * FROM read_csv_auto('{data_dir}/survey_responses.csv')
""")
print("✓ Loaded survey_responses.csv into raw.survey_responses")

# Load teams
conn.execute(f"""
    CREATE TABLE IF NOT EXISTS raw.teams AS
    SELECT * FROM read_csv_auto('{data_dir}/teams.csv')
""")
print("✓ Loaded teams.csv into raw.teams")

# Create stg_employees
conn.execute("""
    CREATE TABLE IF NOT EXISTS analytics.stg_employees AS
    SELECT
        CAST(id AS INTEGER) as employee_id,
        name as employee_name,
        team,
        CAST(manager_id AS INTEGER) as manager_id,
        CAST(start_date AS DATE) as start_date
    FROM raw.employees
""")
print("✓ Created analytics.stg_employees")

# Create stg_survey_responses
conn.execute("""
    CREATE TABLE IF NOT EXISTS analytics.stg_survey_responses AS
    SELECT
        CAST(response_id AS INTEGER) as response_id,
        CAST(employee_id AS INTEGER) as employee_id,
        quarter,
        CAST(satisfaction_score AS INTEGER) as satisfaction_score,
        sentiment_label,
        comment
    FROM raw.survey_responses
""")
print("✓ Created analytics.stg_survey_responses")

# Create fct_survey_metrics
conn.execute("""
    CREATE TABLE IF NOT EXISTS analytics.fct_survey_metrics AS
    WITH survey_data AS (
        SELECT
            r.quarter,
            e.team,
            r.satisfaction_score,
            r.sentiment_label,
            r.response_id
        FROM analytics.stg_survey_responses r
        JOIN analytics.stg_employees e ON r.employee_id = e.employee_id
    ),
    metrics AS (
        SELECT
            quarter,
            team,
            COUNT(DISTINCT response_id) as response_count,
            AVG(CAST(satisfaction_score AS FLOAT)) as avg_satisfaction_score,
            COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END)::FLOAT
                / NULLIF(COUNT(response_id), 0) as pct_positive_sentiment,
            COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END)::FLOAT
                / NULLIF(COUNT(response_id), 0) as pct_neutral_sentiment,
            COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END)::FLOAT
                / NULLIF(COUNT(response_id), 0) as pct_negative_sentiment
        FROM survey_data
        GROUP BY quarter, team
    )
    SELECT * FROM metrics
""")
print("✓ Created analytics.fct_survey_metrics")

# Create dim_org_structure
conn.execute("""
    CREATE TABLE IF NOT EXISTS analytics.dim_org_structure AS
    WITH employees AS (
        SELECT
            employee_id,
            employee_name,
            team,
            manager_id
        FROM analytics.stg_employees
    ),
    org_hierarchy AS (
        SELECT
            e.employee_id,
            e.employee_name,
            e.team,
            e.manager_id,
            m.employee_name as manager_name
        FROM employees e
        LEFT JOIN employees m ON e.manager_id = m.employee_id
    )
    SELECT * FROM org_hierarchy
""")
print("✓ Created analytics.dim_org_structure")

# Verify row counts
print("\n=== Row Counts ===")
emp_count = conn.execute("SELECT COUNT(*) FROM analytics.stg_employees").fetchall()[0][0]
print(f"stg_employees: {emp_count} rows")

survey_count = conn.execute("SELECT COUNT(*) FROM analytics.stg_survey_responses").fetchall()[0][0]
print(f"stg_survey_responses: {survey_count} rows")

metrics_count = conn.execute("SELECT COUNT(*) FROM analytics.fct_survey_metrics").fetchall()[0][0]
print(f"fct_survey_metrics: {metrics_count} rows")

org_count = conn.execute("SELECT COUNT(*) FROM analytics.dim_org_structure").fetchall()[0][0]
print(f"dim_org_structure: {org_count} rows")

# Verify fct_survey_metrics data
print("\n=== fct_survey_metrics (all teams) ===")
result = conn.execute("""
    SELECT DISTINCT team FROM analytics.fct_survey_metrics ORDER BY team
""").fetchall()
for row in result:
    print(f"  {row[0]}")

# Sample query from fct_survey_metrics
print("\n=== Sample from fct_survey_metrics ===")
result = conn.execute("""
    SELECT quarter, team, response_count, avg_satisfaction_score
    FROM analytics.fct_survey_metrics
    ORDER BY quarter, team
    LIMIT 10
""").fetchall()
for row in result:
    print(f"  {row[0]:12} | {row[1]:15} | responses: {row[2]:2} | avg_score: {row[3]:.2f}")

conn.close()
print("\n✓ Database setup complete")
