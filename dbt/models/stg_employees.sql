{{ config(materialized='table') }}

with source as (
    select
        id as employee_id,
        name as employee_name,
        team,
        manager_id,
        start_date
    from {{ source('raw', 'employees') }}
),

renamed as (
    select
        employee_id,
        employee_name,
        team,
        manager_id,
        cast(start_date as date) as start_date
    from source
)

select * from renamed
