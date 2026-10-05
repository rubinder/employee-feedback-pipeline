{{ config(materialized='table') }}

with employees as (
    select
        employee_id,
        employee_name,
        team,
        manager_id
    from {{ ref('stg_employees') }}
),

org_hierarchy as (
    select
        e.employee_id,
        e.employee_name,
        e.team,
        e.manager_id,
        m.employee_name as manager_name
    from employees e
    left join employees m on e.manager_id = m.employee_id
)

select * from org_hierarchy
